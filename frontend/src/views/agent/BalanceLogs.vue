<template>
  <div class="page-container">
    <!-- 余额卡片 -->
    <el-card class="balance-card">
      <div class="balance-info">
        <span class="label">当前余额</span>
        <span class="value">{{ authStore.balance }}</span>
        <span class="unit">点</span>
      </div>
      <div class="balance-tip">每创建一个订单消耗 1 点余额</div>
    </el-card>

    <!-- 变动记录 -->
    <el-card>
      <template #header>
        <span>余额变动记录</span>
      </template>
      <el-table :data="list" v-loading="loading" stripe style="width:100%">
        <el-table-column label="时间" width="160">
          <template #default="{ row }">{{ row.created_at }}</template>
        </el-table-column>
        <el-table-column label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.change_amount > 0 ? 'success' : 'danger'" size="small">
              {{ row.change_amount > 0 ? '充值' : '消费' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="100">
          <template #default="{ row }">
            <span :style="{ color: row.change_amount > 0 ? '#67c23a' : '#f56c6c', fontWeight: 'bold' }">
              {{ row.change_amount > 0 ? '+' : '' }}{{ row.change_amount }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="变动后余额" width="100">
          <template #default="{ row }">{{ row.balance_after }}</template>
        </el-table-column>
        <el-table-column label="原因" min-width="150">
          <template #default="{ row }">{{ row.reason }}</template>
        </el-table-column>
        <el-table-column label="操作人" width="100">
          <template #default="{ row }">{{ row.operator || '-' }}</template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size"
          :total="pagination.total" :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next"
          @change="loadList" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { agentApi } from '../../api'
import { useAgentAuthStore } from '../../stores/agentAuth'

const authStore = useAgentAuthStore()

const loading = ref(false)
const list = ref([])
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

async function loadList() {
  loading.value = true
  try {
    const res = await agentApi.balanceLogs({
      page: pagination.page,
      page_size: pagination.page_size,
    })
    list.value = res.list
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadList()
  authStore.fetchMe()
})
</script>

<style scoped>
.page-container { display: flex; flex-direction: column; gap: 16px; }
.balance-card { text-align: center; padding: 20px 0; }
.balance-info { margin-bottom: 8px; }
.balance-info .label { color: #909399; font-size: 14px; }
.balance-info .value { font-size: 48px; font-weight: bold; color: #e6a23c; margin: 0 8px; }
.balance-info .unit { font-size: 16px; color: #909399; }
.balance-tip { color: #c0c4cc; font-size: 12px; }
.pagination { display: flex; justify-content: flex-end; margin-top: 16px; }
</style>
