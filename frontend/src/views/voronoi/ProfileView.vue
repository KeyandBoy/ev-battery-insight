<template>
  <div class="profile-page">
    <el-row :gutter="24">
      <!-- 用户信息卡片 -->
      <el-col :xs="24" :sm="24" :md="10" :lg="8">
        <el-card shadow="never" class="profile-card">
          <div class="profile-avatar-section">
            <div class="profile-avatar">
              <el-icon :size="48"><UserFilled /></el-icon>
            </div>
            <h3>{{ authStore.user?.username }}</h3>
            <p class="profile-email">{{ authStore.user?.email }}</p>
            <el-tag type="success" effect="plain" size="small" style="margin-top:8px">已认证用户</el-tag>
          </div>
          <el-divider />
          <div class="profile-meta">
            <div class="meta-row">
              <span class="meta-label">注册时间</span>
              <span class="meta-value">{{ formatDate(authStore.user?.created_at) }}</span>
            </div>
            <div class="meta-row">
              <span class="meta-label">上次更新</span>
              <span class="meta-value">{{ formatDate(authStore.user?.updated_at) }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 编辑区域 -->
      <el-col :xs="24" :sm="24" :md="14" :lg="16">
        <!-- 修改资料 -->
        <el-card shadow="never" style="margin-bottom:20px">
          <template #header>
            <div style="display:flex;align-items:center;gap:8px">
              <el-icon><Edit /></el-icon>
              <span style="font-weight:600">修改资料</span>
            </div>
          </template>
          <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" label-width="80px" style="max-width:480px">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="profileForm.username" placeholder="3-20位" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="profileLoading" @click="handleUpdateProfile">保存修改</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 修改密码 -->
        <el-card shadow="never">
          <template #header>
            <div style="display:flex;align-items:center;gap:8px">
              <el-icon><Lock /></el-icon>
              <span style="font-weight:600">修改密码</span>
            </div>
          </template>
          <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="80px" style="max-width:480px">
            <el-form-item label="当前密码" prop="old_password">
              <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入当前密码" />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="至少6位" />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="再次输入新密码" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '../../stores/voronoi/auth'
import { updateProfile, changePassword } from '../../api/voronoi/auth'
import { ElMessage } from 'element-plus'
import { UserFilled, Edit, Lock } from '@element-plus/icons-vue'

const authStore = useAuthStore()

const profileFormRef = ref(null)
const passwordFormRef = ref(null)
const profileLoading = ref(false)
const passwordLoading = ref(false)

const profileForm = reactive({
  username: '',
  email: '',
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const profileRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度3-20位', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) callback(new Error('两次输入的密码不一致'))
  else callback()
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

onMounted(async () => {
  try {
    await authStore.fetchProfile()
  } catch { /* use cached */ }
  profileForm.username = authStore.user?.username || ''
  profileForm.email = authStore.user?.email || ''
})

async function handleUpdateProfile() {
  const valid = await profileFormRef.value.validate().catch(() => false)
  if (!valid) return
  profileLoading.value = true
  try {
    const res = await updateProfile({
      username: profileForm.username,
      email: profileForm.email,
    })
    authStore.user = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
    ElMessage.success('资料更新成功')
  } catch (err) {
    ElMessage.error(err?.message || '更新失败')
  } finally {
    profileLoading.value = false
  }
}

async function handleChangePassword() {
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return
  passwordLoading.value = true
  try {
    await changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    passwordFormRef.value.resetFields()
  } catch (err) {
    ElMessage.error(err?.message || '密码修改失败')
  } finally {
    passwordLoading.value = false
  }
}

function formatDate(iso) {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}
</script>
