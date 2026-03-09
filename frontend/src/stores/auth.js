import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('admin_token') || '')
  const username = ref(localStorage.getItem('admin_username') || '')

  async function login(usr, pwd) {
    const formData = new FormData()
    formData.append('username', usr)
    formData.append('password', pwd)
    const res = await authApi.login(formData)
    token.value = res.access_token
    username.value = res.username
    localStorage.setItem('admin_token', res.access_token)
    localStorage.setItem('admin_username', res.username)
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_username')
  }

  return { token, username, login, logout }
})
