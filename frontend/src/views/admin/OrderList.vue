<template>
  <div class="page-container">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-row :gutter="12" align="middle">
        <el-col :span="5">
          <el-input v-model="filters.keyword" placeholder="搜索订单编号" clearable prefix-icon="Search"
            @keyup.enter="loadList" />
        </el-col>
        <el-col :span="3">
          <el-select v-model="filters.link_status" placeholder="链接状态" clearable style="width:100%">
            <el-option label="未填写" value="未填写" />
            <el-option label="已提交" value="已提交" />
            <el-option label="已过期" value="已过期" />
            <el-option label="已禁用" value="已禁用" />
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-select v-model="filters.exec_status" placeholder="执行状态" clearable style="width:100%">
            <el-option label="待执行" value="待执行" />
            <el-option label="执行中" value="执行中" />
            <el-option label="成功" value="成功" />
            <el-option label="失败" value="失败" />
          </el-select>
        </el-col>
        <el-col :span="3">
          <el-select v-model="filters.system_type" placeholder="系统类型" clearable style="width:100%">
            <el-option label="安卓Q区" value="安卓Q区" />
            <el-option label="苹果Q区" value="苹果Q区" />
            <el-option label="安卓V区" value="安卓V区" />
            <el-option label="苹果V区" value="苹果V区" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.creator" placeholder="创建者" clearable style="width:100%">
            <el-option label="管理员" value="admin" />
            <el-option v-for="agent in agentList" :key="agent.id" :label="agent.username" :value="agent.username" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" icon="Search" @click="loadList">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>
      <el-row style="margin-top:12px" :gutter="12">
        <el-col :span="24">
          <el-button type="success" icon="Plus" @click="$router.push('/admin/orders/create')">创建订单</el-button>
          <el-button type="primary" icon="DocumentAdd" @click="batchDialogVisible = true">批量创建</el-button>
          <el-button type="warning" icon="Download" @click="handleExport" :loading="exporting">导出全部</el-button>
          <template v-if="selectedIds.length > 0">
            <el-divider direction="vertical" />
            <span style="color:#606266;font-size:13px;margin-right:8px">已选 {{ selectedIds.length }} 条</span>
            <el-button type="warning" icon="Download" @click="handleExportSelected" :loading="exportingSelected">
              导出所选
            </el-button>
            <el-popconfirm :title="`确认删除选中的 ${selectedIds.length} 个订单？`" @confirm="handleBatchDelete">
              <template #reference>
                <el-button type="danger" icon="Delete" :loading="batchDeleting">批量删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-col>
      </el-row>
    </el-card>

    <!-- 订单表格 -->
    <el-card>
      <el-table
        :data="list"
        v-loading="loading"
        stripe
        style="width:100%"
        @selection-change="handleSelectionChange"
        ref="tableRef"
      >
        <el-table-column type="selection" width="46" />
        <el-table-column label="序号" width="60" align="center">
          <template #default="{ $index }">
            {{ (pagination.page - 1) * pagination.page_size + $index + 1 }}
          </template>
        </el-table-column>
        <el-table-column prop="order_no" label="订单编号" width="200" />
        <el-table-column label="专属链接" width="320">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:8px">
              <el-input :value="row.client_link" readonly size="small" style="width:200px;font-size:12px" />
              <el-button type="primary" size="small" @click="copyLink(row.client_link)">
                <el-icon><CopyDocument /></el-icon> 复制
              </el-button>
              <el-button type="success" size="small" @click="openLink(row.client_link)">
                <el-icon><Open /></el-icon> 打开
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="链接状态" width="100">
          <template #default="{ row }">
            <el-tag :type="linkStatusType(row.link_status)" size="small">{{ row.link_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="system_type" label="系统类型" width="100">
          <template #default="{ row }">
            <span>{{ row.system_type || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="图片" width="80">
          <template #default="{ row }">
            <el-image v-if="row.image_url" :src="getImageUrl(row.image_url)"
              :preview-src-list="[getImageUrl(row.image_url)]" style="width:40px;height:40px;border-radius:4px"
              fit="cover" />
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="执行状态" width="100">
          <template #default="{ row }">
            <el-tag :type="execStatusType(row.exec_status)" size="small">{{ row.exec_status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建者" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.agent_name" type="warning" size="small">{{ row.agent_name }}</el-tag>
            <span v-else style="color:#909399">管理员</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160" />
        <el-table-column prop="submitted_at" label="提交时间" width="160">
          <template #default="{ row }">{{ row.submitted_at || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="260">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="$router.push(`/admin/orders/${row.id}`)">详情</el-button>
            <el-button type="warning" link size="small" @click="copyLink(row.client_link)">复制链接</el-button>
            <el-button type="success" link size="small" @click="handleRetry(row)"
              :disabled="row.exec_status === '执行中'">重新执行</el-button>
            <el-button type="danger" link size="small" @click="handleDisable(row)"
              :disabled="row.link_status === '已禁用'">禁用链接</el-button>
            <el-popconfirm title="确认删除该订单？" @confirm="handleDelete(row)">
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

    <!-- 批量创建对话框 -->
    <el-dialog v-model="batchDialogVisible" title="批量创建订单" width="440px" :close-on-click-modal="false">
      <el-form :model="batchForm" label-width="100px">
        <el-form-item label="创建数量">
          <el-input-number v-model="batchForm.count" :min="1" :max="100" :step="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="batchForm.remark" type="textarea" :rows="3" placeholder="可选，所有订单共用此备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleBatchCreate" :loading="batchLoading">确认创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { orderApi, getImageUrl, agentManageApi } from '../../api'

const tableRef = ref(null)
const loading = ref(false)
const list = ref([])
const filters = reactive({ keyword: '', link_status: '', exec_status: '', system_type: '', creator: '' })
const pagination = reactive({ page: 1, page_size: 20, total: 0 })
const agentList = ref([]) // 代理列表用于创建者筛选

// 勾选
const selectedIds = ref([])
function handleSelectionChange(rows) {
  selectedIds.value = rows.map(r => r.id)
}

// 批量创建
const batchDialogVisible = ref(false)
const batchLoading = ref(false)
const batchForm = reactive({ count: 10, remark: '' })

// 导出
const exporting = ref(false)
const exportingSelected = ref(false)

// 批量删除
const batchDeleting = ref(false)

async function loadList() {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.page_size }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.link_status) params.link_status = filters.link_status
    if (filters.exec_status) params.exec_status = filters.exec_status
    if (filters.system_type) params.system_type = filters.system_type
    if (filters.creator) params.creator = filters.creator
    const res = await orderApi.list(params)
    list.value = res.list
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  Object.assign(filters, { keyword: '', link_status: '', exec_status: '', system_type: '', creator: '' })
  pagination.page = 1
  loadList()
}

function copyLink(link) {
  navigator.clipboard.writeText(link).then(() => {
    ElMessage.success('链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败，请手动复制')
  })
}

function openLink(link) {
  window.open(link, '_blank')
}

async function handleRetry(row) {
  await orderApi.retry(row.id)
  ElMessage.success('已重新加入执行队列')
  loadList()
}

async function handleDisable(row) {
  await ElMessageBox.confirm('确认禁用该订单链接？禁用后客户无法访问', '提示', { type: 'warning' })
  await orderApi.disable(row.id)
  ElMessage.success('链接已禁用')
  loadList()
}

async function handleDelete(row) {
  await orderApi.delete(row.id)
  ElMessage.success('订单已删除')
  loadList()
}

async function handleBatchDelete() {
  batchDeleting.value = true
  try {
    const res = await orderApi.batchDelete(selectedIds.value)
    ElMessage.success(res.message || `成功删除${res.count}个订单`)
    selectedIds.value = []
    loadList()
  } finally {
    batchDeleting.value = false
  }
}

function linkStatusType(status) {
  return { '未填写': 'info', '已提交': 'success', '已过期': 'warning', '已禁用': 'danger' }[status] || 'info'
}

function execStatusType(status) {
  return { '待执行': 'info', '执行中': 'warning', '成功': 'success', '失败': 'danger' }[status] || 'info'
}

async function handleBatchCreate() {
  batchLoading.value = true
  try {
    const res = await orderApi.batchCreate({
      count: batchForm.count,
      remark: batchForm.remark || undefined,
    })
    ElMessage.success(res.message || `成功创建${res.count}个订单`)
    batchDialogVisible.value = false
    batchForm.count = 10
    batchForm.remark = ''
    pagination.page = 1
    loadList()
  } finally {
    batchLoading.value = false
  }
}

async function downloadBlob(promise) {
  const res = await promise
  const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  const disposition = res.headers['content-disposition']
  const filename = disposition ? decodeURIComponent(disposition.split('filename=')[1]?.replace(/"/g, '') || 'orders.xlsx') : 'orders.xlsx'
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

async function handleExport() {
  exporting.value = true
  try {
    const params = {}
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.link_status) params.link_status = filters.link_status
    if (filters.exec_status) params.exec_status = filters.exec_status
    if (filters.system_type) params.system_type = filters.system_type
    if (filters.creator) params.creator = filters.creator
    await downloadBlob(orderApi.exportOrders(params))
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

async function handleExportSelected() {
  exportingSelected.value = true
  try {
    await downloadBlob(orderApi.exportByIds(selectedIds.value))
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    exportingSelected.value = false
  }
}

async function loadAgentList() {
  try {
    const res = await agentManageApi.list({ page: 1, page_size: 1000 })
    agentList.value = res.list || []
  } catch (e) {
    console.error('加载代理列表失败', e)
  }
}

onMounted(() => {
  loadList()
  loadAgentList()
})
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.search-card { }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
