import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const isAuthenticated = computed(() => !!token.value)

  // 初始化时，如果token存在，设置axios默认授权头
  if (token.value) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }

  // 设置 token
  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('token', newToken)

    // 设置 axios 默认授权头
    axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
  }

  // 设置用户信息
  const setUser = (userData) => {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  // 登录方法
  const login = async (credentials) => {
    try {
      const response = await axios.post('/api/login', credentials)
      if (response.data.access_token) {
        setToken(response.data.access_token)
        // 可以在这里获取用户信息
        if (response.data.user_id) {
          // 如果有用户信息，可以调用获取用户详情的接口
          await fetchUserInfo(response.data.user_id)
        }
        return { success: true }
      }
    } catch (error) {
      console.error('Login failed:', error)
      return {
        success: false,
        error: error.response?.data?.detail || '登录失败'
      }
    }
  }

  // 获取用户信息
  const fetchUserInfo = async (userId) => {
    try {
      const response = await axios.get(`/api/users/me`)
      setUser(response.data)
    } catch (error) {
      console.error('Failed to fetch user info:', error)
    }
  }

  // 注册方法
  const register = async (userData) => {
    try {
      const response = await axios.post('/api/register', userData)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Registration failed:', error)
      return {
        success: false,
        error: error.response?.data?.detail || '注册失败'
      }
    }
  }

  // 登出方法
  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    delete axios.defaults.headers.common['Authorization']
  }

  // 检查认证状态
  const checkAuth = () => {
    return isAuthenticated.value
  }

  // 获取当前用户ID（用于API调用）
  const getCurrentUserId = () => {
    return user.value?.id || ''
  }

  return {
    token,
    user,
    isAuthenticated,
    setToken,
    setUser,
    login,
    register,
    logout,
    checkAuth,
    getCurrentUserId
  }
})