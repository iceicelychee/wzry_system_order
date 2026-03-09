<template>
  <el-container style="height:100vh">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <div>代理后台</div>
        <div class="balance-info">余额: {{ authStore.balance }} 点</div>
      </div>
      <el-menu :default-active="activeMenu" router background-color="#1a3a2a" text-color="#c0c4cc"
        active-text-color="#ffffff">
        <el-menu-item index="/agent/orders">
          <el-icon><List /></el-icon>
          <span>订单列表</span>
        </el-menu-item>
        <el-menu-item index="/agent/orders/create">
          <el-icon><Plus /></el-icon>
          <span>创建订单</span>
        </el-menu-item>
        <el-menu-item index="/agent/balance">
          <el-icon><Wallet /></el-icon>
          <span>余额明细</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="page-title">{{ pageTitle }}</span>
        <div class="header-right">
          <el-tag type="warning" size="large">余额: {{ authStore.balance }} 点</el-tag>
          <span class="username">{{ authStore.username }}</span>
          <el-button type="text" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAgentAuthStore } from '../../stores/agentAuth'

const route = useRoute()
const router = useRouter()
const authStore = useAgentAuthStore()

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => {
  const map = {
    '/agent/orders': '订单列表',
    '/agent/orders/create': '创建订单',
    '/agent/balance': '余额明细',
  }
  if (route.path.startsWith('/agent/orders/') && route.path !== '/agent/orders') {
    return '订单详情'
  }
  return map[route.path] || '订单详情'
})

function handleLogout() {
  authStore.logout()
  router.push('/agent/login')
}

onMounted(() => {
  // 刷新余额信息
  authStore.fetchMe().catch(() => {})
})
</script>

<style scoped>
.sidebar {
  background: #1a3a2a;
  display: flex;
  flex-direction: column;
}
.logo {
  color: #fff;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.logo > div:first-child {
  font-size: 16px;
  font-weight: bold;
}
.balance-info {
  font-size: 12px;
  color: #67c23a;
  margin-top: 8px;
}
.header {
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
.page-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.username {
  color: #606266;
  font-size: 14px;
}
.main-content {
  background: #f5f7fa;
}
</style>
