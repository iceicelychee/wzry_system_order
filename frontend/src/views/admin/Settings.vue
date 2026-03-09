<template>
  <div class="settings-page">
    <el-card shadow="never">
      <template #header>
        <span>订单状态页 - 底部说明内容</span>
      </template>
      <el-input
        v-model="noticeContent"
        type="textarea"
        :rows="8"
        placeholder="请输入说明内容，支持换行显示。留空则不显示说明版块。"
      />
      <div style="margin-top: 16px; display: flex; align-items: center; gap: 12px;">
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        <span class="hint-text">此内容将显示在客户订单处理状态页面底部</span>
      </div>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px;">
      <template #header>
        <span>预览效果</span>
      </template>
      <div v-if="noticeContent" class="preview-box">
        <div class="preview-title">说明</div>
        <div class="preview-content" v-html="previewHtml"></div>
      </div>
      <el-empty v-else description="暂无说明内容" :image-size="60" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { authApi } from '../../api'
import { ElMessage } from 'element-plus'

const noticeContent = ref('')
const saving = ref(false)

const previewHtml = computed(() => {
  return noticeContent.value.replace(/\n/g, '<br>')
})

onMounted(async () => {
  try {
    const res = await authApi.getSiteConfig('order_status_notice')
    if (res.value) noticeContent.value = res.value
  } catch {}
})

async function handleSave() {
  saving.value = true
  try {
    await authApi.updateSiteConfig('order_status_notice', noticeContent.value)
    ElMessage.success('保存成功')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.settings-page {
  max-width: 800px;
}
.hint-text {
  font-size: 12px;
  color: #909399;
}
.preview-box {
  padding: 16px;
  background: #f4f4f5;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}
.preview-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}
.preview-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}
</style>
