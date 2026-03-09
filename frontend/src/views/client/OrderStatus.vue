<template>
  <div class="status-page">
    <div class="status-card">
      <div class="card-header">
        <h2>订单处理状态</h2>
        <p class="order-no">订单编号：{{ orderNo }}</p>
      </div>

      <!-- 步骤条 -->
      <el-steps :active="currentStep" align-center style="margin-bottom:28px">
        <el-step title="已提交" icon="Document" />
        <el-step title="等待扫码" icon="Cellphone" />
        <el-step title="执行中" icon="Loading" />
        <el-step title="完成" icon="CircleCheck" />
      </el-steps>

      <!-- 等待启动 -->
      <div v-if="execStatus === '待执行'" class="state-box">
        <el-icon class="spin-icon"><Loading /></el-icon>
        <p class="state-text">正在准备脚本，请稍候...</p>
      </div>

      <!-- 二维码扫码 -->
      <div v-else-if="execStatus === '执行中' && showQrcode" class="state-box">
        <p class="state-label">请使用手机扫描下方二维码登录</p>
        <div class="qrcode-wrap">
          <el-image :src="qrcodeUrl" style="width:200px;height:200px" fit="contain" />
          <div v-if="qrcodeStatus === '已过期'" class="qrcode-expired">
            <span>二维码已过期</span>
          </div>
        </div>
        <div class="qrcode-status-row">
          <el-tag :type="qrcodeTagType" size="large">{{ qrcodeStatusText }}</el-tag>
        </div>
        <p v-if="countdown > 0" class="countdown">二维码有效期剩余 <strong>{{ countdown }}</strong> 秒</p>
        <p v-if="qrcodeStatus === '已过期'" class="expired-hint">二维码已过期，请等待系统重新生成...</p>
      </div>

      <!-- 执行中（无二维码） -->
      <div v-else-if="execStatus === '执行中' && !showQrcode" class="state-box">
        <el-icon class="spin-icon"><Loading /></el-icon>
        <p class="state-text">登录成功，正在执行操作...</p>
      </div>

      <!-- 执行成功 -->
      <div v-else-if="execStatus === '成功'" class="state-box">
        <el-icon style="font-size:64px;color:#67c23a"><CircleCheck /></el-icon>
        <p class="state-text success">执行成功！</p>
        <p v-if="resultText" class="result-text">{{ resultText }}</p>
      </div>

      <!-- 执行失败 -->
      <div v-else-if="execStatus === '失败'" class="state-box">
        <el-icon style="font-size:64px;color:#f56c6c"><CircleClose /></el-icon>
        <p class="state-text error">执行失败</p>
        <p v-if="errorText" class="error-text">{{ errorText }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { clientApi, getImageUrl, getWsUrl } from '../../api'

const route = useRoute()
const token = route.params.token

const orderNo = ref('')
const execStatus = ref('待执行')
const qrcodeUrl = ref('')
const qrcodeStatus = ref('')
const qrcodeExpiredAt = ref(null)
const countdown = ref(0)
const resultText = ref('')
const errorText = ref('')

let ws = null
let pollTimer = null
let countdownTimer = null

const showQrcode = computed(() => !!qrcodeUrl.value)

const currentStep = computed(() => {
  if (execStatus.value === '待执行') return 0
  if (execStatus.value === '执行中' && showQrcode.value && qrcodeStatus.value !== '已确认') return 1
  if (execStatus.value === '执行中') return 2
  if (execStatus.value === '成功' || execStatus.value === '失败') return 3
  return 0
})

const qrcodeTagType = computed(() => ({
  '待扫码': 'warning', '已扫码': 'primary', '已确认': 'success', '已过期': 'danger'
})[qrcodeStatus.value] || 'info')

const qrcodeStatusText = computed(() => ({
  '待扫码': '等待扫码中...', '已扫码': '已扫码，请在手机上确认登录', '已确认': '登录确认成功', '已过期': '二维码已过期'
})[qrcodeStatus.value] || qrcodeStatus.value)

function startCountdown() {
  if (!qrcodeExpiredAt.value) return
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    const diff = Math.floor((new Date(qrcodeExpiredAt.value) - Date.now()) / 1000)
    countdown.value = diff > 0 ? diff : 0
    if (diff <= 0) clearInterval(countdownTimer)
  }, 1000)
}

function applyStatus(data) {
  if (data.exec_status) execStatus.value = data.exec_status
  if (data.qrcode_url) qrcodeUrl.value = getImageUrl(data.qrcode_url)
  if (data.qrcode_status) qrcodeStatus.value = data.qrcode_status
  if (data.qrcode_expired_at) { qrcodeExpiredAt.value = data.qrcode_expired_at; startCountdown() }
  if (data.result) resultText.value = data.result
  if (data.error_msg) errorText.value = data.error_msg
}

function connectWebSocket() {
  ws = new WebSocket(getWsUrl(token))
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data)
    if (msg.type === 'qrcode') {
      execStatus.value = '执行中'
      qrcodeUrl.value = getImageUrl(msg.qrcode_url)
      qrcodeStatus.value = '待扫码'
      qrcodeExpiredAt.value = msg.expired_at
      countdown.value = msg.expire_seconds
      startCountdown()
    } else if (msg.type === 'status') {
      const statusMap = {
        qrcode_scanned: '已扫码', qrcode_confirmed: '已确认', qrcode_expired: '已过期', running: ''
      }
      if (msg.status === 'running') execStatus.value = '执行中'
      if (statusMap[msg.status]) qrcodeStatus.value = statusMap[msg.status]
    } else if (msg.type === 'result') {
      execStatus.value = msg.success ? '成功' : '失败'
      resultText.value = msg.result || ''
      errorText.value = msg.error_msg || ''
    }
  }
  ws.onclose = () => {
    // WebSocket断开时降级为轮询
    startPolling()
  }
}

function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(async () => {
    if (execStatus.value === '成功' || execStatus.value === '失败') {
      clearInterval(pollTimer)
      return
    }
    try {
      const data = await clientApi.getStatus(token)
      applyStatus(data)
    } catch { }
  }, 3000)
}

onMounted(async () => {
  try {
    const info = await clientApi.getOrder(token)
    orderNo.value = info.order_no
  } catch { }

  try {
    const data = await clientApi.getStatus(token)
    applyStatus(data)
  } catch { }

  connectWebSocket()
})

onUnmounted(() => {
  if (ws) ws.close()
  if (pollTimer) clearInterval(pollTimer)
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>

<style scoped>
.status-page {
  min-height: 100vh;
  background: #f0f2f5;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 24px 16px;
}
.status-card {
  background: #fff;
  border-radius: 12px;
  padding: 28px 24px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.card-header { text-align: center; margin-bottom: 24px; }
.card-header h2 { font-size: 20px; color: #303133; margin: 0 0 4px; }
.order-no { color: #909399; font-size: 13px; margin: 0; }
.state-box { text-align: center; padding: 24px 0; }
.spin-icon { font-size: 56px; color: #409eff; animation: spin 1.2s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.state-text { font-size: 16px; color: #606266; margin-top: 16px; }
.state-text.success { color: #67c23a; font-weight: 600; }
.state-text.error { color: #f56c6c; font-weight: 600; }
.state-label { font-size: 15px; color: #303133; font-weight: 500; margin-bottom: 16px; }
.qrcode-wrap { position: relative; display: inline-block; margin: 0 auto; }
.qrcode-expired {
  position: absolute; inset: 0;
  background: rgba(0,0,0,0.55);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 16px; border-radius: 8px;
}
.qrcode-status-row { margin-top: 14px; }
.countdown { color: #909399; font-size: 13px; margin-top: 10px; }
.expired-hint { color: #e6a23c; font-size: 13px; margin-top: 6px; }
.result-text { color: #606266; font-size: 14px; margin-top: 8px; }
.error-text { color: #f56c6c; font-size: 13px; margin-top: 8px; background: #fef0f0; padding: 8px 12px; border-radius: 6px; }
</style>
