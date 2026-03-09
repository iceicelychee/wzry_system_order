<template>
  <div class="page-container" v-loading="loading">
    <el-page-header @back="$router.push('/agent/orders')">
      <template #content>
        <span class="page-title">订单详情</span>
      </template>
    </el-page-header>

    <el-row :gutter="20" style="margin-top:20px">
      <!-- 左侧：基本信息 -->
      <el-col :span="14">
        <el-card>
          <template #header>
            <span>基本信息</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="订单编号">{{ order.order_no }}</el-descriptions-item>
            <el-descriptions-item label="系统类型">{{ order.system_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="链接状态">
              <el-tag :type="linkStatusType(order.link_status)">{{ order.link_status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="执行状态">
              <el-tag :type="execStatusType(order.exec_status)">{{ order.exec_status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ order.created_at }}</el-descriptions-item>
            <el-descriptions-item label="提交时间">{{ order.submitted_at || '-' }}</el-descriptions-item>
            <el-descriptions-item label="备注" :span="2">{{ order.remark || '-' }}</el-descriptions-item>
            <el-descriptions-item label="客户链接" :span="2">
              <el-input :value="order.client_link" readonly size="small" style="width:300px" />
              <el-button type="primary" size="small" style="margin-left:8px" @click="copyLink(order.client_link)">复制</el-button>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 执行日志 -->
        <el-card style="margin-top:20px">
          <template #header>
            <span>执行日志</span>
          </template>
          <div v-if="execLogs.length" class="log-list">
            <div v-for="(log, idx) in execLogs" :key="idx" class="log-item">
              <span class="log-time">{{ log.time }}</span>
              <span class="log-content">{{ log.content }}</span>
            </div>
          </div>
          <el-empty v-else description="暂无执行日志" />
        </el-card>
      </el-col>

      <!-- 右侧：图片和二维码 -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <span>客户上传图片</span>
          </template>
          <el-image v-if="order.image_url" :src="getImageUrl(order.image_url)"
            :preview-src-list="[getImageUrl(order.image_url)]" fit="contain"
            style="width:100%;max-height:300px" />
          <el-empty v-else description="暂无图片" />
        </el-card>

        <el-card style="margin-top:20px" v-if="latestCallback">
          <template #header>
            <span>二维码状态</span>
          </template>
          <el-tag :type="qrcodeStatusType(latestCallback.qrcode_status)" size="large">
            {{ latestCallback.qrcode_status || '-' }}
          </el-tag>
          <div v-if="latestCallback.qrcode_url" style="margin-top:12px">
            <el-image :src="getImageUrl(latestCallback.qrcode_url)" style="width:200px" fit="contain" />
          </div>
          <div v-if="latestCallback.qrcode_expired_at" style="margin-top:8px;color:#909399;font-size:12px">
            过期时间: {{ latestCallback.qrcode_expired_at }}
          </div>
          <div v-if="latestCallback.result" style="margin-top:12px;color:#67c23c">
            结果: {{ latestCallback.result }}
          </div>
          <div v-if="latestCallback.error_msg" style="margin-top:12px;color:#f56c6c">
            错误: {{ latestCallback.error_msg }}
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { agentApi, getImageUrl } from '../../api'

const route = useRoute()

const loading = ref(false)
const order = ref({})
const execLogs = ref([])
const callbacks = ref([])

const latestCallback = computed(() => callbacks.value[0] || null)

async function loadDetail() {
  loading.value = true
  try {
    const res = await agentApi.orderDetail(route.params.id)
    order.value = res
    execLogs.value = res.exec_logs || []
    callbacks.value = res.callbacks || []
  } finally {
    loading.value = false
  }
}

function copyLink(link) {
  navigator.clipboard.writeText(link).then(() => {
    ElMessage.success('链接已复制')
  })
}

function linkStatusType(status) {
  return { '未填写': 'info', '已提交': 'success', '已过期': 'warning', '已禁用': 'danger' }[status] || 'info'
}

function execStatusType(status) {
  return { '待执行': 'info', '执行中': 'warning', '成功': 'success', '失败': 'danger' }[status] || 'info'
}

function qrcodeStatusType(status) {
  return { '待扫码': 'info', '已扫码': 'warning', '已确认': 'success', '已过期': 'danger' }[status] || 'info'
}

onMounted(loadDetail)
</script>

<style scoped>
.page-container { padding: 20px; }
.page-title { font-size: 18px; font-weight: 500; }
.log-list { max-height: 300px; overflow-y: auto; }
.log-item { padding: 8px 0; border-bottom: 1px solid #f0f0f0; }
.log-time { color: #909399; font-size: 12px; margin-right: 12px; }
.log-content { color: #303133; }
</style>
