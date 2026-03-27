import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  // 管理员路由
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('../views/admin/Login.vue'),
  },
  {
    path: '/admin',
    component: () => import('../views/admin/Layout.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      {
        path: '',
        redirect: '/admin/orders',
      },
      {
        path: 'orders',
        name: 'OrderList',
        component: () => import('../views/admin/OrderList.vue'),
      },
      {
        path: 'orders/create',
        name: 'OrderCreate',
        component: () => import('../views/admin/OrderCreate.vue'),
      },
      {
        path: 'orders/:id',
        name: 'OrderDetail',
        component: () => import('../views/admin/OrderDetail.vue'),
      },
      {
        path: 'gallery',
        name: 'Gallery',
        component: () => import('../views/admin/Gallery.vue'),
      },
      {
        path: 'agents',
        name: 'AgentList',
        component: () => import('../views/admin/AgentList.vue'),
      },
      {
        path: 'agents/:id',
        name: 'AgentDetail',
        component: () => import('../views/admin/AgentDetail.vue'),
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/admin/Settings.vue'),
      },
      {
        path: 'api-doc',
        name: 'ApiDoc',
        component: () => import('../views/admin/ApiDoc.vue'),
      },
    ],
  },
  // 代理路由
  {
    path: '/agent/login',
    name: 'AgentLogin',
    component: () => import('../views/agent/Login.vue'),
  },
  {
    path: '/agent',
    component: () => import('../views/agent/Layout.vue'),
    meta: { requiresAuth: true, role: 'agent' },
    children: [
      {
        path: '',
        redirect: '/agent/orders',
      },
      {
        path: 'orders',
        name: 'AgentOrderList',
        component: () => import('../views/agent/OrderList.vue'),
      },
      {
        path: 'orders/create',
        name: 'AgentOrderCreate',
        component: () => import('../views/agent/OrderCreate.vue'),
      },
      {
        path: 'orders/:id',
        name: 'AgentOrderDetail',
        component: () => import('../views/agent/OrderDetail.vue'),
      },
      {
        path: 'balance',
        name: 'AgentBalance',
        component: () => import('../views/agent/BalanceLogs.vue'),
      },
    ],
  },
  // 客户路由
  {
    path: '/order/:token',
    name: 'ClientOrder',
    component: () => import('../views/client/OrderForm.vue'),
  },
  {
    path: '/order/:token/status',
    name: 'ClientStatus',
    component: () => import('../views/client/OrderStatus.vue'),
  },
  {
    path: '/',
    redirect: '/admin',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth) {
    const role = to.meta.role
    if (role === 'admin') {
      const token = localStorage.getItem('admin_token')
      if (!token) {
        next('/admin/login')
        return
      }
    } else if (role === 'agent') {
      const token = localStorage.getItem('agent_token')
      if (!token) {
        next('/agent/login')
        return
      }
    }
  }
  next()
})

export default router
