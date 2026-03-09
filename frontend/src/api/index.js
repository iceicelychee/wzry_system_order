import axios from 'axios'
import { ElMessage } from 'element-plus'

// 走 Vite 代理，BASE_URL 留空即可
const BASE_URL = ''
const API_SERVER = 'http://localhost:8000'

// 管理员 HTTP 实例
const http = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || '请求失败，请重试'
    if (err.response?.status === 401) {
      localStorage.removeItem('admin_token')
      window.location.href = '/admin/login'
      return Promise.reject(err)
    }
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

// 代理 HTTP 实例
const agentHttp = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

agentHttp.interceptors.request.use((config) => {
  const token = localStorage.getItem('agent_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

agentHttp.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || '请求失败，请重试'
    if (err.response?.status === 401) {
      localStorage.removeItem('agent_token')
      localStorage.removeItem('agent_username')
      localStorage.removeItem('agent_balance')
      window.location.href = '/agent/login'
      return Promise.reject(err)
    }
    ElMessage.error(msg)
    return Promise.reject(err)
  }
)

export const authApi = {
  login: (formData) => http.post('/api/auth/login', formData),
  getMe: () => http.get('/api/auth/me'),
  changePassword: (data) => http.post('/api/auth/change-password', data),
  // 代理登录
  agentLogin: (data) => axios.post(`${BASE_URL}/api/auth/agent-login`, data).then(r => r.data),
}

export const orderApi = {
  create: (formData) => http.post('/api/order/create', formData),
  list: (params) => http.get('/api/order/list', { params }),
  detail: (id) => http.get(`/api/order/detail/${id}`),
  update: (id, data) => http.put(`/api/order/update/${id}`, data),
  disable: (id) => http.post(`/api/order/disable/${id}`),
  delete: (id) => http.delete(`/api/order/delete/${id}`),
  retry: (id) => http.post(`/api/order/retry/${id}`),
  batchCreate: (data) => http.post('/api/order/batch-create', data),
  batchDelete: (ids) => http.post('/api/order/batch-delete', { ids }),
  exportOrders: (params) => axios.get('/api/order/export', {
    params,
    responseType: 'blob',
    headers: { Authorization: `Bearer ${localStorage.getItem('admin_token')}` },
  }),
  exportByIds: (ids, params) => axios.post('/api/order/export-by-ids', { ids }, {
    params,
    responseType: 'blob',
    headers: { Authorization: `Bearer ${localStorage.getItem('admin_token')}` },
  }),
}

export const galleryApi = {
  categoryList: () => http.get('/api/gallery/category/list'),
  createCategory: (data) => http.post('/api/gallery/category/create', data),
  deleteCategory: (id) => http.delete(`/api/gallery/category/delete/${id}`),
  list: (params) => http.get('/api/gallery/list', { params }),
  upload: (formData) => http.post('/api/gallery/upload', formData),
  delete: (id) => http.delete(`/api/gallery/delete/${id}`),
  batchDelete: (ids) => http.post('/api/gallery/batch-delete', { ids }),
  batchCategory: (ids, categoryId) => http.post('/api/gallery/batch-category', { ids, category_id: categoryId }),
}

export const clientApi = {
  getOrder: (token) => http.get(`/api/client/order/${token}`),
  submit: (token, formData) => http.post(`/api/client/order/${token}/submit`, formData),
  getStatus: (token) => http.get(`/api/client/order/${token}/status`),
}

// 管理员管理代理的 API
export const agentManageApi = {
  create: (data) => http.post('/api/agent/create', data),
  list: (params) => http.get('/api/agent/list', { params }),
  detail: (id) => http.get(`/api/agent/detail/${id}`),
  update: (id, data) => http.put(`/api/agent/update/${id}`, data),
  recharge: (id, data) => http.post(`/api/agent/recharge/${id}`, data),
  delete: (id) => http.delete(`/api/agent/delete/${id}`),
  resetPassword: (id, data) => http.post(`/api/agent/reset-password/${id}`, data),
}

// 代理自身操作的 API
export const agentApi = {
  me: () => agentHttp.get('/api/agent/me'),
  changePassword: (data) => agentHttp.post('/api/agent/change-password', data),
  balanceLogs: (params) => agentHttp.get('/api/agent/my-balance-logs', { params }),
  myOrders: (params) => agentHttp.get('/api/agent/my-orders', { params }),
  orderDetail: (id) => agentHttp.get(`/api/agent/my-orders/${id}`),
  createOrder: (formData) => agentHttp.post('/api/agent/my-orders/create', formData),
  batchCreate: (data) => agentHttp.post('/api/agent/my-orders/batch-create', data),
  exportOrders: (params) => axios.get('/api/agent/my-orders/export', {
    params,
    responseType: 'blob',
    headers: { Authorization: `Bearer ${localStorage.getItem('agent_token')}` },
  }),
}

export const getImageUrl = (path) => {
  if (!path) return ''
  if (path.startsWith('http')) return path
  return `${API_SERVER}${path}`
}

export const getWsUrl = (token) => {
  return `ws://localhost:8000/api/callback/ws/${token}`
}

export default http
