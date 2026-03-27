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
        <el-menu-item index="/admin/settings">
          <el-icon><Setting /></el-icon>
          <span>站点设置</span>
        </el-menu-item>
        <el-menu-item index="/admin/api-doc">
          <el-icon><Document /></el-icon>
          <span>脚本对接说明</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span class="page-title">{{ pageTitle }}</span>
        <div class="header-right">
          <span class="username">{{ authStore.username }}</span>
          <el-button type="text" @click="showChangePwd = true">修改密码</el-button>
          <el-button type="text" @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="showChangePwd" title="修改密码" width="400px" :close-on-click-modal="false">
      <el-form :model="pwdForm" :rules="pwdRules" ref="pwdFormRef" label-width="80px">
        <el-form-item label="原密码" prop="old_password">
          <el-input v-model="pwdForm.old_password" type="password" show-password placeholder="请输入原密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="pwdForm.new_password" type="password" show-password placeholder="请输入新密码（至少6位）" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="pwdForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showChangePwd = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="handleChangePwd">确认修改</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { computed, ref, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { authApi } from '../../api'
import { ElMessage } from 'element-plus'
import { List, Plus, Picture, User, Setting, Document } from '@element-plus/icons-vue'

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
    '/admin/settings': '站点设置',
    '/admin/api-doc': '脚本对接说明',
  }
  if (route.path.startsWith('/admin/agents/') && route.path !== '/admin/agents') {
    return '代理详情'
  }
  if (route.path.startsWith('/admin/orders/') && route.path !== '/admin/orders') {
    return '订单详情'
  }
  return map[route.path] || '订单详情'
})

// 修改密码
const showChangePwd = ref(false)
const pwdLoading = ref(false)
const pwdFormRef = ref()
const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const pwdRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== pwdForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

async function handleChangePwd() {
  await pwdFormRef.value.validate()
  pwdLoading.value = true
  try {
    await authApi.changePassword({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    showChangePwd.value = false
    Object.assign(pwdForm, { old_password: '', new_password: '', confirm_password: '' })
    authStore.logout()
    router.push('/admin/login')
  } finally {
    pwdLoading.value = false
  }
}

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
