import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('admin-token') || null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin || false)

  // 初始化时从localStorage恢复token
  if (token.value) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    checkAuth()
  }

  async function login(username, password) {
    try {
      const response = await api.post('/auth/login', { username, password })
      const { user: userData, token: tokenData } = response.data
      
      // 检查是否是管理员
      if (!userData.is_admin) {
        return {
          success: false,
          error: '需要管理员权限才能访问管理后台'
        }
      }
      
      user.value = userData
      token.value = tokenData
      localStorage.setItem('admin-token', tokenData)
      api.defaults.headers.common['Authorization'] = `Bearer ${tokenData}`
      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || '登录失败'
      }
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('admin-token')
    delete api.defaults.headers.common['Authorization']
  }

  async function checkAuth() {
    try {
      const response = await api.get('/auth/me')
      if (!response.data.is_admin) {
        logout()
        return false
      }
      user.value = response.data
      return true
    } catch (error) {
      logout()
      return false
    }
  }

  return {
    user,
    token,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    checkAuth
  }
})
