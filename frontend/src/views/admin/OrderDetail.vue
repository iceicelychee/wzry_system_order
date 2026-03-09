<template>
  <div class="page-container" v-loading="loading">
    <el-page-header @back="$router.push('/admin/orders')" content="订单详情" style="margin-bottom:16px" />

    <el-row :gutter="16">
      <el-col :span="14">
        <el-card>
          <template #header>基本信息</template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="订单编号">{{ order.order_no }}</el-descriptions-item>
            <el-descriptions-item label="系统类型">{{ order.system_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="链接状态">
              <el-tag :type="linkStatusType(order.link_status)" size="small">{{ order.link_status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="执行状态">
              <el-tag :type="execStatusType(order.exec_status)" size="small">{{ order.exec_status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ order.created_at }}</el-descriptions-item>
            <el-descriptions-item label="提交时间">{{ order.submitted_at || '-' }}</el-descriptions-item>
            <el-descriptions-item label="备注" :span="2">{{ order.remark || '-' }}</el-descriptions-item>
            <el-descriptions-item label="客户链接" :span="2">
              <el-input :value="order.client_link" readonly>
                <template #append>
                  <el-button icon="CopyDocument" @click="copyLink(order.client_link)">复制</el-button>
                </template>
              </el-input>
            </el-descriptions-item>
          </el-descriptions>

          <div style="margin-top:16px;display:flex;gap:8px">
            <el-button type="success" icon="RefreshRight" @click="handleRetry"
              :disabled="order.exec_status === '执行中'">重新执行</el-button>
            <el-button type="warning" icon="Remove" @click="handleDisable"
              :disabled="order.link_status === '已禁用'">禁用链接</el-button>
            <el-popconfirm title="确认删除？" @confirm="handleDelete">
              <template #reference>
                <el-button type="danger" icon="Delete">删除订单</el-button>
              </template>
            </el-popconfirm>
          </div>
        </el-card>

        <!-- 执行日志 -->
        <el-card style="margin-top:16px">
          <template #header>执行日志</template>
          <div class="log-list">
            <div v-for="(log, i) in order.exec_logs" :key="i" class="log-item">
              <span class="log-time">{{ log.time }}</span>
              <span class="log-content">{{ log.content }}</span>
            </div>
            <el-empty v-if="!order.exec_logs?.length" description="暂无日志" />
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <!-- 图片 -->
        <el-card>
          <template #header>客户上传图片</template>
          <el-image v-if="order.image_url" :src="getImageUrl(order.image_url)"
            :preview-src-list="[getImageUrl(order.image_url)]" style="width:100%;border-radius:6px" fit="contain" />
          <el-empty v-else description="暂未上传图片" />
        </el-card>

        <!-- 二维码 -->
        <el-card style="margin-top:16px">
          <template #header>
            登录二维码
            <el-tag v-if="latestCb" :type="qrcodeStatusType(latestCb.qrcode_status)" size="small" style="margin-left:8px">
              {{ latestCb.qrcode_status }}
            </el-tag>
          </template>
          <el-image v-if="latestCb?.qrcode_url" :src="getImageUrl(latestCb.qrcode_url)"
            style="width:200px;height:200px;display:block;margin:0 auto" fit="contain" />
          <el-empty v-else description="暂无二维码" />
          <div v-if="latestCb?.qrcode_expired_at" style="text-align:center;color:#909399;font-size:13px;margin-top:8px">
            过期时间：{{ latestCb.qrcode_expired_at }}
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { orderApi, getImageUrl } from '../../api'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const order = ref({})

const latestCb = computed(() => {
  const cbs = order.value.callbacks
  return cbs && cbs.length ? cbs[cbs.length - 1] : null
})

async function loadDetail() {
  loading.value = true
  try {
    order.value = await orderApi.detail(route.params.id)
  } finally {
    loading.value = false
  }
}

function copyLink(link) {
  navigator.clipboard.writeText(link).then(() => ElMessage.success('链接已复制'))
}

async function handleRetry() {
  await orderApi.retry(route.params.id)
  ElMessage.success('已重新加入执行队列')
  loadDetail()
}

async function handleDisable() {
  await ElMessageBox.confirm('确认禁用该订单链接？', '提示', { type: 'warning' })
  await orderApi.disable(route.params.id)
  ElMessage.success('链接已禁用')
  loadDetail()
}

async function handleDelete() {
  await orderApi.delete(route.params.id)
  ElMessage.success('订单已删除')
  router.push('/admin/orders')
}

function linkStatusType(s) {
  return { '未填写': 'info', '已提交': 'success', '已过期': 'warning', '已禁用': 'danger' }[s] || 'info'
}
function execStatusType(s) {
  return { '待执行': 'info', '执行中': 'warning', '成功': 'success', '失败': 'danger' }[s] || 'info'
}
function qrcodeStatusType(s) {
  return { '待扫码': 'warning', '已扫码': 'primary', '已确认': 'success', '已过期': 'danger' }[s] || 'info'
}

onMounted(loadDetail)
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; }
.log-list { max-height: 300px; overflow-y: auto; }
.log-item { display: flex; gap: 12px; padding: 6px 0; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
.log-time { color: #909399; white-space: nowrap; }
.log-content { color: #606266; }
</style>
