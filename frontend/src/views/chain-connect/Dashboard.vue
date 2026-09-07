<template>
  <div class="dashboard">
    <!-- 顶部导航栏 -->
    <header class="top-bar">
      <div class="top-bar-left">
        <el-icon :size="24" color="#409EFF"><Share /></el-icon>
        <span class="brand">ChainConnect</span>
        <el-tag type="info" size="small" effect="plain">网络数据可视化构件</el-tag>
      </div>
      <div class="top-bar-right">
        <el-dropdown trigger="click" @command="handleUserCommand">
          <span class="user-info">
            <el-avatar :size="32" style="background: linear-gradient(135deg, #409EFF, #67C23A);">
              {{ userStore.user?.username?.charAt(0)?.toUpperCase() }}
            </el-avatar>
            <span class="username">{{ userStore.user?.username }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon> 个人信息
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon> 退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- 主内容区域：三栏布局 -->
    <div class="main-content">
      <!-- 左侧功能面板 -->
      <LeftSidebar />

      <!-- 中间可视化区域 -->
      <CenterCanvas />

      <!-- 右侧数据面板 -->
      <RightPanel />
    </div>

    <!-- 个人信息对话框 -->
    <el-dialog v-model="profileDialogVisible" title="个人信息" width="420px" destroy-on-close>
      <el-form :model="profileForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input :model-value="userStore.user?.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdateProfile">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '../../stores/chain-connect/user'
import { authApi } from '../../api/chain-connect'
import LeftSidebar from '../../components/chain-connect/LeftSidebar.vue'
import CenterCanvas from '../../components/chain-connect/CenterCanvas.vue'
import RightPanel from '../../components/chain-connect/RightPanel.vue'

const router = useRouter()
const userStore = useUserStore()

const profileDialogVisible = ref(false)
const profileForm = reactive({
  email: ''
})

function handleUserCommand(command) {
  if (command === 'profile') {
    profileForm.email = userStore.user?.email || ''
    profileDialogVisible.value = true
  } else if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      userStore.logout()
      router.push('/login')
      ElMessage.success('已退出登录')
    }).catch(() => {})
  }
}

async function handleUpdateProfile() {
  try {
    const res = await authApi.updateProfile({ email: profileForm.email })
    if (res.code === 200) {
      userStore.setAuth(userStore.token, res.data)
      ElMessage.success('更新成功')
      profileDialogVisible.value = false
    }
  } catch (e) {
    // 错误在拦截器处理
  }
}
</script>

<style scoped>
.dashboard {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.top-bar {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  flex-shrink: 0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  z-index: 100;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}

.top-bar-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.2s;
}

.user-info:hover {
  background: #f5f7fa;
}

.username {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}
</style>
