<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="brand-icon">🎯</div>
        <h2>综合可视化平台</h2>
        <p class="subtitle">通用多源数据可视化与分析工具</p>
      </div>

      <el-form :model="form" :rules="rules" ref="formRef" class="login-form">
        <el-form-item prop="username">
          <el-input 
            v-model="form.username" 
            placeholder="请输入用户名" 
            prefix-icon="User" 
            size="large"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="请输入密码" 
            prefix-icon="Lock" 
            size="large" 
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            class="login-btn" 
            :loading="loading" 
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="register-entry">
        <span>还没有账号？</span>
        <el-button link type="primary" @click="router.push('/register')">立即注册</el-button>
      </div>

      <div class="module-preview">
        <p class="preview-title">平台包含以下模块：</p>
        <div class="module-tags">
          <el-tag effect="plain" size="small">关系网络分析</el-tag>
          <el-tag effect="plain" size="small">数据流画布</el-tag>
          <el-tag effect="plain" size="small">高维区域可视化</el-tag>
          <el-tag effect="plain" size="small">Voronoi图分析</el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3到20个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 30, message: '密码长度在6到30个字符之间', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form)
    })
    const data = await res.json()

    if (data.code === 200) {
      localStorage.setItem('token', data.data.token)
      localStorage.setItem('user', JSON.stringify(data.data.user))
      
      ElMessage.success(data.message || '登录成功')
      
      let redirectPath = route.query.redirect || '/chain-connect'

      setTimeout(() => {
        window.location.href = redirectPath
      }, 300)
      
    } else {
      ElMessage.error(data.message || '登录失败，请检查用户名和密码')
    }
  } catch (e) {
    console.error('Login error:', e)
    
    if (import.meta.env.DEV) {
      const testUser = {
        id: 1,
        username: form.username,
        email: `${form.username}@test.com`,
        display_name: form.username,
        role: 'admin'
      }
      localStorage.setItem('token', 'dev-test-token-' + Date.now())
      localStorage.setItem('user', JSON.stringify(testUser))
      ElMessage.success('开发模式：模拟登录成功')
      
      setTimeout(() => {
        window.location.href = '/chain-connect'
      }, 300)
    } else {
      ElMessage.error('网络连接失败，请检查网络后重试')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.login-box {
  width: 420px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.98);
  border-radius: 16px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.brand-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.login-box h2 {
  color: #1a202c;
  font-size: 26px;
  margin-bottom: 8px;
}

.subtitle {
  color: #718096;
  font-size: 14px;
}

.login-btn {
  width: 100%;
}

.register-entry {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin: -8px 0 22px;
  color: #718096;
  font-size: 14px;
}

.module-preview {
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
}

.preview-title {
  text-align: center;
  color: #a0aec0;
  font-size: 13px;
  margin-bottom: 14px;
}

.module-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}
</style>
