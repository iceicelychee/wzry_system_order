<template>
  <div class="page-container">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-row :gutter="12" align="middle">
        <el-col :span="6">
          <el-input v-model="filters.keyword" placeholder="搜索用户名" clearable prefix-icon="Search" @keyup.enter="loadList" />
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.status" placeholder="状态" clearable style="width:100%">
            <el-option label="启用" value="启用" />
            <el-option label="禁用" value="禁用" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" icon="Search" @click="loadList">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>
      <el-row style="margin-top:12px">
        <el-col :span="24">
          <el-button type="success" icon="Plus" @click="openCreateDialog">创建代理</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 代理列表 -->
    <el-card>
      <el-table :data="list" v-loading="loading" stripe style="width:100%">
        <el-table-column label="序号" width="60" align="center">
          <template #default="{ $index }">
            {{ (pagination.page - 1) * pagination.page_size + $index + 1 }}
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column label="余额" width="120">
          <template #default="{ row }">
            <el-tag type="warning" size="large">{{ row.balance }} 点</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '启用' ? 'success' : 'danger'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="150">
          <template #default="{ row }">{{ row.remark || '-' }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column label="操作" fixed="right" width="280">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="$router.push(`/admin/agents/${row.id}`)">详情</el-button>
            <el-button type="warning" link size="small" @click="openRechargeDialog(row)">充值</el-button>
            <el-button type="info" link size="small" @click="openResetPasswordDialog(row)">重置密码</el-button>
            <el-button :type="row.status === '启用' ? 'danger' : 'success'" link size="small" @click="toggleStatus(row)">
              {{ row.status === '启用' ? '禁用' : '启用' }}
            </el-button>
            <el-popconfirm title="确认删除该代理？" @confirm="handleDelete(row)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size"
          :total="pagination.total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
          @change="loadList" />
      </div>
    </el-card>

    <!-- 创建代理对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建代理" width="440px" :close-on-click-modal="false">
      <el-form :model="createForm" label-width="80px">
        <el-form-item label="用户名" required>
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" required>
          <el-input v-model="createForm.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="初始余额">
          <el-input-number v-model="createForm.balance" :min="0" :max="10000" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="createForm.remark" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="createLoading">确认创建</el-button>
      </template>
    </el-dialog>

    <!-- 充值对话框 -->
    <el-dialog v-model="rechargeDialogVisible" title="调整余额" width="400px" :close-on-click-modal="false">
      <el-form :model="rechargeForm" label-width="80px">
        <el-form-item label="代理">
          <span>{{ rechargeTarget?.username }} (当前余额: {{ rechargeTarget?.balance }} 点)</span>
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
        <el-form-item label="代理">
          <span>{{ resetPasswordTarget?.username }}</span>
        </el-form-item>
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
import { ElMessage } from 'element-plus'
import { agentManageApi } from '../../api'

const loading = ref(false)
const list = ref([])
const filters = reactive({ keyword: '', status: '' })
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

// 创建代理
const createDialogVisible = ref(false)
const createLoading = ref(false)
const createForm = reactive({ username: '', password: '', balance: 0, remark: '' })

// 充值
const rechargeDialogVisible = ref(false)
const rechargeLoading = ref(false)
const rechargeTarget = ref(null)
const rechargeForm = reactive({ amount: 0, reason: '' })

// 重置密码
const resetPasswordDialogVisible = ref(false)
const resetPasswordLoading = ref(false)
const resetPasswordTarget = ref(null)
const resetPasswordForm = reactive({ new_password: '' })

async function loadList() {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.page_size }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status
    const res = await agentManageApi.list(params)
    list.value = res.list
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  Object.assign(filters, { keyword: '', status: '' })
  pagination.page = 1
  loadList()
}

function openCreateDialog() {
  Object.assign(createForm, { username: '', password: '', balance: 0, remark: '' })
  createDialogVisible.value = true
}

async function handleCreate() {
  if (!createForm.username || !createForm.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  createLoading.value = true
  try {
    await agentManageApi.create(createForm)
    ElMessage.success('代理创建成功')
    createDialogVisible.value = false
    loadList()
  } finally {
    createLoading.value = false
  }
}

function openRechargeDialog(row) {
  rechargeTarget.value = row
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
    const res = await agentManageApi.recharge(rechargeTarget.value.id, rechargeForm)
    ElMessage.success(`余额调整成功，当前余额: ${res.balance} 点`)
    rechargeDialogVisible.value = false
    loadList()
  } finally {
    rechargeLoading.value = false
  }
}

function openResetPasswordDialog(row) {
  resetPasswordTarget.value = row
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
    await agentManageApi.resetPassword(resetPasswordTarget.value.id, resetPasswordForm)
    ElMessage.success('密码重置成功')
    resetPasswordDialogVisible.value = false
  } finally {
    resetPasswordLoading.value = false
  }
}

async function toggleStatus(row) {
  const newStatus = row.status === '启用' ? '禁用' : '启用'
  await agentManageApi.update(row.id, { status: newStatus })
  ElMessage.success(`已${newStatus}`)
  loadList()
}

async function handleDelete(row) {
  await agentManageApi.delete(row.id)
  ElMessage.success('代理已删除')
  loadList()
}

onMounted(loadList)
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
