<template>
  <div class="page-container" v-loading="loading">
    <el-page-header @back="$router.push('/admin/agents')">
      <template #content>
        <span class="page-title">代理详情</span>
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
            <el-descriptions-item label="用户名">{{ agent.username }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="agent.status === '启用' ? 'success' : 'danger'">{{ agent.status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="余额">
              <el-tag type="warning" size="large">{{ agent.balance }} 点</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ agent.created_at }}</el-descriptions-item>
            <el-descriptions-item label="备注" :span="2">{{ agent.remark || '-' }}</el-descriptions-item>
          </el-descriptions>

          <div style="margin-top:20px">
            <el-button type="warning" @click="openRechargeDialog">充值/扣减</el-button>
            <el-button type="info" @click="openResetPasswordDialog">重置密码</el-button>
            <el-button :type="agent.status === '启用' ? 'danger' : 'success'" @click="toggleStatus">
              {{ agent.status === '启用' ? '禁用账号' : '启用账号' }}
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：余额变动记录 -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <span>余额变动记录</span>
          </template>
          <el-table :data="balanceLogs" max-height="400" size="small">
            <el-table-column label="时间" width="150">
              <template #default="{ row }">{{ row.created_at }}</template>
            </el-table-column>
            <el-table-column label="金额" width="80">
              <template #default="{ row }">
                <span :style="{ color: row.change_amount > 0 ? '#67c23a' : '#f56c6c' }">
                  {{ row.change_amount > 0 ? '+' : '' }}{{ row.change_amount }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="余额" width="80">
              <template #default="{ row }">{{ row.balance_after }}</template>
            </el-table-column>
            <el-table-column label="原因" min-width="120">
              <template #default="{ row }">{{ row.reason }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 充值对话框 -->
    <el-dialog v-model="rechargeDialogVisible" title="调整余额" width="400px" :close-on-click-modal="false">
      <el-form :model="rechargeForm" label-width="80px">
        <el-form-item label="当前余额">
          <span>{{ agent.balance }} 点</span>
        </el-form-item>
        <el-form-item label="调整数量" required>
          <el-input-number v-model="rechargeForm.amount" :min="-10000" :max="10000" style="width:100%" />
          <div style="color:#909399;font-size:12px;margin-top:4px">正数为充值，负数为扣减</div>
        </el-form-item>
        <el-form-item label="原因">
          <el-input v-model="rechargeForm.reason" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rechargeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRecharge" :loading="rechargeLoading">确认</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetPasswordDialogVisible" title="重置密码" width="400px" :close-on-click-modal="false">
      <el-form :model="resetPasswordForm" label-width="80px">
        <el-form-item label="新密码" required>
          <el-input v-model="resetPasswordForm.new_password" type="password" placeholder="请输入新密码" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPasswordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleResetPassword" :loading="resetPasswordLoading">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { agentManageApi } from '../../api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const agent = ref({})
const balanceLogs = ref([])

// 充值
const rechargeDialogVisible = ref(false)
const rechargeLoading = ref(false)
const rechargeForm = reactive({ amount: 0, reason: '' })

// 重置密码
const resetPasswordDialogVisible = ref(false)
const resetPasswordLoading = ref(false)
const resetPasswordForm = reactive({ new_password: '' })

async function loadDetail() {
  loading.value = true
  try {
    const res = await agentManageApi.detail(route.params.id)
    agent.value = res.agent
    balanceLogs.value = res.balance_logs
  } finally {
    loading.value = false
  }
}

function openRechargeDialog() {
  rechargeForm.amount = 0
  rechargeForm.reason = ''
  rechargeDialogVisible.value = true
}

async function handleRecharge() {
  if (rechargeForm.amount === 0) {
    ElMessage.warning('请输入调整数量')
    return
  }
  rechargeLoading.value = true
  try {
    const res = await agentManageApi.recharge(agent.value.id, rechargeForm)
    ElMessage.success(`余额调整成功，当前余额: ${res.balance} 点`)
    rechargeDialogVisible.value = false
    loadDetail()
  } finally {
    rechargeLoading.value = false
  }
}

function openResetPasswordDialog() {
  resetPasswordForm.new_password = ''
  resetPasswordDialogVisible.value = true
}

async function handleResetPassword() {
  if (!resetPasswordForm.new_password) {
    ElMessage.warning('请输入新密码')
    return
  }
  resetPasswordLoading.value = true
  try {
    await agentManageApi.resetPassword(agent.value.id, resetPasswordForm)
    ElMessage.success('密码重置成功')
    resetPasswordDialogVisible.value = false
  } finally {
    resetPasswordLoading.value = false
  }
}

async function toggleStatus() {
  const newStatus = agent.value.status === '启用' ? '禁用' : '启用'
  await agentManageApi.update(agent.value.id, { status: newStatus })
  ElMessage.success(`已${newStatus}`)
  loadDetail()
}

onMounted(loadDetail)
</script>

<style scoped>
.page-container { padding: 20px; }
.page-title { font-size: 18px; font-weight: 500; }
</style>
