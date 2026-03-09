<template>
  <div class="page-container">
    <el-alert type="info" :closable="false" style="margin-bottom:16px">
      当前余额: <b style="color:#e6a23c">{{ authStore.balance }}</b> 点，创建订单消耗 1 点
    </el-alert>

    <el-card>
      <el-form :model="form" label-width="100px" style="max-width:600px">
        <el-form-item label="订单编号">
          <el-input v-model="form.order_no" placeholder="留空自动生成" />
        </el-form-item>
        <el-form-item label="系统类型">
          <el-select v-model="form.system_type" placeholder="可选，客户也可填写" clearable style="width:100%">
            <el-option label="安卓Q区" value="安卓Q区" />
            <el-option label="苹果Q区" value="苹果Q区" />
            <el-option label="安卓V区" value="安卓V区" />
            <el-option label="苹果V区" value="苹果V区" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
        <el-form-item label="图片">
          <el-upload ref="uploadRef" :auto-upload="false" :show-file-list="true" :limit="1"
            accept=".jpg,.jpeg,.png,.bmp,.gif,.webp" :on-change="handleFileChange">
            <el-button type="primary">选择图片</el-button>
            <template #tip>
              <div style="color:#909399;font-size:12px">支持 jpg/png/bmp/gif/webp，可选</div>
            </template>
          </el-upload>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting" :disabled="authStore.balance < 1">
            创建订单
          </el-button>
          <span v-if="authStore.balance < 1" style="color:#f56c6c;margin-left:12px">余额不足，请充值</span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 成功弹窗 -->
    <el-dialog v-model="successDialogVisible" title="创建成功" width="500px" :close-on-click-modal="false">
      <el-result icon="success" title="订单创建成功" :sub-title="`订单编号: ${createdOrder?.order_no}`">
        <template #extra>
          <div style="margin-bottom:20px">
            <el-input :value="createdOrder?.client_link" readonly style="width:400px">
              <template #append>
                <el-button @click="copyLink">复制链接</el-button>
              </template>
            </el-input>
          </div>
          <el-button type="primary" @click="successDialogVisible = false; resetForm()">继续创建</el-button>
          <el-button @click="$router.push('/agent/orders')">返回列表</el-button>
        </template>
      </el-result>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { agentApi } from '../../api'
import { useAgentAuthStore } from '../../stores/agentAuth'

const authStore = useAgentAuthStore()

const uploadRef = ref()
const submitting = ref(false)
const form = reactive({
  order_no: '',
  system_type: '',
  remark: '',
})
const selectedFile = ref(null)

const successDialogVisible = ref(false)
const createdOrder = ref(null)

function handleFileChange(file) {
  selectedFile.value = file.raw
}

async function handleSubmit() {
  if (authStore.balance < 1) {
    ElMessage.warning('余额不足')
    return
  }

  submitting.value = true
  try {
    const formData = new FormData()
    if (form.order_no) formData.append('order_no', form.order_no)
    if (form.system_type) formData.append('system_type', form.system_type)
    if (form.remark) formData.append('remark', form.remark)
    if (selectedFile.value) formData.append('image', selectedFile.value)

    const res = await agentApi.createOrder(formData)
    ElMessage.success('订单创建成功')
    createdOrder.value = res.order
    authStore.updateBalance(authStore.balance - 1)
    successDialogVisible.value = true
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  form.order_no = ''
  form.system_type = ''
  form.remark = ''
  selectedFile.value = null
  uploadRef.value?.clearFiles()
}

function copyLink() {
  if (createdOrder.value?.client_link) {
    navigator.clipboard.writeText(createdOrder.value.client_link)
    ElMessage.success('链接已复制')
  }
}
</script>

<style scoped>
.page-container { padding: 20px; }
</style>
