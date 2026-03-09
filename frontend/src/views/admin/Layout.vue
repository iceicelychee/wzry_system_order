<template>
  <el-container style="height:100vh">
    <el-aside width="220px" class="sidebar">
      <div class="logo">订单管理系统</div>
      <el-menu :default-active="activeMenu" router background-color="#1d2d50" text-color="#c0c4cc"
        active-text-color="#ffffff">
        <el-menu-item index="/admin/orders">
          <el-icon><List /></el-icon>
          <span>订单列表</span>
        </el-menu-item>
        <el-menu-item index="/admin/orders/create">
          <el-icon><Plus /></el-icon>
          <span>创建订单</span>
        </el-menu-item>
        <el-menu-item index="/admin/gallery">
          <el-icon><Picture /></el-icon>
          <span>图库管理</span>
        </el-menu-item>
        <el-menu-item index="/admin/agents">
          <el-icon><User /></el-icon>
          <span>代理管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="page-title">{{ pageTitle }}</span>
        <div class="header-right">
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
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => {
  const map = {
    '/admin/orders': '订单列表',
    '/admin/orders/create': '创建订单',
    '/admin/gallery': '图库管理',
    '/admin/agents': '代理管理',
  }
  if (route.path.startsWith('/admin/agents/') && route.path !== '/admin/agents') {
    return '代理详情'
  }
  if (route.path.startsWith('/admin/orders/') && route.path !== '/admin/orders') {
    return '订单详情'
  }
  return map[route.path] || '订单详情'
})

function handleLogout() {
  authStore.logout()
  router.push('/admin/login')
}
</script>

<style scoped>
.sidebar {
  background: #1d2d50;
  display: flex;
  flex-direction: column;
}
.logo {
  color: #fff;
  font-size: 16px;
  font-weight: bold;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
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
