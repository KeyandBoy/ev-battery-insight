import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../../router'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：自动添加 token
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器：统一处理错误
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      } else if (status === 409) {
        ElMessage.error(data.message || '资源冲突')
      } else {
        ElMessage.error(data.message || '请求失败')
      }
    } else {
      ElMessage.error('网络连接失败')
    }
    return Promise.reject(error)
  }
)

// ========== 认证接口 ==========
export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getProfile: () => api.get('/auth/profile'),
  updateProfile: (data) => api.put('/auth/profile', data)
}

// ========== 数据集接口 ==========
export const datasetApi = {
  getAll: () => api.get('/datasets'),
  getById: (id) => api.get(`/datasets/${id}`)
}

// ========== 项目管理接口 ==========
export const projectApi = {
  getAll: () => api.get('/projects'),
  getById: (id) => api.get(`/projects/${id}`),
  create: (data) => api.post('/projects', data),
  update: (id, data) => api.put(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`)
}

// ========== 文本处理接口 ==========
export const textApi = {
  extract: (data) => api.post('/text/extract', data)
}

// ========== 图分析接口 ==========
export const analysisApi = {
  getStats: (graphData) => api.post('/analysis/stats', { graph_data: graphData })
}

// ========== 数据导入导出接口 ==========
export const importExportApi = {
  importJson: (graphData) => api.post('/import/json', { graph_data: graphData }),
  exportJson: (graphData) => api.post('/export/json', { graph_data: graphData })
}

export default api
