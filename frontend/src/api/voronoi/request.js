import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../../router'

const request = axios.create({
  baseURL: '/api/voronoi',
  timeout: 30000,
})

request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

let isRedirectingToLogin = false

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const { response } = error
    if (response) {
      if (response.status === 401 && !isRedirectingToLogin) {
        isRedirectingToLogin = true
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        ElMessage.error('登录已过期，请重新登录')
        router.push({ name: 'Login' }).finally(() => { isRedirectingToLogin = false })
      }
      return Promise.reject(response.data)
    }
    ElMessage.error('网络连接失败')
    return Promise.reject(error)
  },
)

export default request
