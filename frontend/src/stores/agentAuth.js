import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi, agentApi } from '../api'

export const useAgentAuthStore = defineStore('agentAuth', () => {
  const token = ref(localStorage.getItem('agent_token') || '')
  const username = ref(localStorage.getItem('agent_username') || '')
  const balance = ref(parseInt(localStorage.getItem('agent_balance') || '0'))

  async function login(usr, pwd) {
    const res = await authApi.agentLogin({ username: usr, password: pwd })
    token.value = res.access_token
    username.value = res.username
    balance.value = res.balance
    localStorage.setItem('agent_token', res.access_token)
    localStorage.setItem('agent_username', res.username)
    localStorage.setItem('agent_balance', res.balance)
  }

  function logout() {
    token.value = ''
    username.value = ''
    balance.value = 0
    localStorage.removeItem('agent_token')
    localStorage.removeItem('agent_username')
    localStorage.removeItem('agent_balance')
  }

  async function fetchMe() {
    const res = await agentApi.me()
    username.value = res.username
    balance.value = res.balance
    localStorage.setItem('agent_username', res.username)
    localStorage.setItem('agent_balance', res.balance)
    return res
  }

  function updateBalance(newBalance) {
    balance.value = newBalance
    localStorage.setItem('agent_balance', newBalance)
  }

  return { token, username, balance, login, logout, fetchMe, updateBalance }
})
