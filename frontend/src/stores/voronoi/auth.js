import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '../../api/voronoi/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')

  let storedUser = null
  try { storedUser = JSON.parse(localStorage.getItem('user') || 'null') } catch { /* corrupted */ }
  const user = ref(storedUser)

  const isAuthenticated = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '')

  function saveAuth(tokenVal, userVal) {
    token.value = tokenVal
    user.value = userVal
    localStorage.setItem('token', tokenVal)
    localStorage.setItem('user', JSON.stringify(userVal))
  }

  async function login(credentials) {
    const res = await authApi.login(credentials)
    saveAuth(res.data.token, res.data.user)
    return res
  }

  async function register(data) {
    const res = await authApi.register(data)
    saveAuth(res.data.token, res.data.user)
    return res
  }

  async function fetchProfile() {
    const res = await authApi.getProfile()
    user.value = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
    return res
  }

  async function updateProfile(data) {
    const res = await authApi.updateProfile(data)
    user.value = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
    return res
  }

  async function changePassword(data) {
    return await authApi.changePassword(data)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    token, user, isAuthenticated, username,
    login, register, fetchProfile, updateProfile, changePassword, logout,
  }
})