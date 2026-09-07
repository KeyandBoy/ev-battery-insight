<template>
  <div :class="['layout-wrapper', { 'fullscreen-mode': isFullscreen }]">
    <template v-if="isFullscreen">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" @toggle-fullscreen="toggleFullscreen" />
        </transition>
      </router-view>
    </template>

    <el-container v-else class="layout-container">
      <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
        <div class="logo">
          <span v-if="!isCollapse">综合可视化平台</span>
          <span v-else>可视化</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :collapse-transition="false"
          router
          class="menu"
        >
          <el-menu-item index="/home">
            <el-icon><HomeFilled /></el-icon>
            <template #title>首页</template>
          </el-menu-item>

          <el-menu-item index="/chain-connect">
            <el-icon><Share /></el-icon>
            <template #title>图神经网络可视化</template>
          </el-menu-item>

          <el-sub-menu index="dataflow">
            <template #title>
              <el-icon><DataLine /></el-icon>
              <span>数据流画布</span>
            </template>
            <el-menu-item index="/dataflow">项目首页</el-menu-item>
            <el-menu-item index="/dataflow/editor">大屏编辑器</el-menu-item>
            <el-menu-item index="/dataflow/datasets">数据集管理</el-menu-item>
            <el-menu-item index="/dataflow/treemap">Treemap分析</el-menu-item>
            <el-menu-item index="/dataflow/profile">个人资料</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="region">
            <template #title>
              <el-icon><Histogram /></el-icon>
              <span>高维区域可视化</span>
            </template>
            <el-menu-item index="/region">分析工作台</el-menu-item>
            <el-menu-item index="/region/dashboard">控制台</el-menu-item>
            <el-menu-item index="/region/experiment">对比实验</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="voronoi">
            <template #title>
              <el-icon><Grid /></el-icon>
              <span>Voronoi图分析</span>
            </template>
            <el-menu-item index="/voronoi/analysis">数据分析</el-menu-item>
            <el-menu-item index="/voronoi/dashboard">仪表盘</el-menu-item>
            <el-menu-item index="/voronoi/data">数据管理</el-menu-item>
            <el-menu-item index="/voronoi/visualization">可视化展示</el-menu-item>
            <el-menu-item index="/voronoi/profile">个人资料</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <el-container>
        <el-header class="header">
          <div class="header-left">
            <el-icon class="collapse-btn" @click="toggleCollapse">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
            <el-breadcrumb separator="/">
              <el-breadcrumb-item :to="{ path: '/home' }">首页</el-breadcrumb-item>
              <el-breadcrumb-item v-if="currentRoute.meta.title">
                {{ currentRoute.meta.title }}
              </el-breadcrumb-item>
            </el-breadcrumb>
            
            <el-tooltip
              v-if="showFullscreenToggle"
              content="切换全屏模式"
              placement="bottom"
            >
              <el-button 
                size="small" 
                circle
                @click="toggleFullscreen"
              >
                <el-icon><FullScreen /></el-icon>
              </el-button>
            </el-tooltip>
          </div>

          <div class="header-right">
            <el-dropdown trigger="click" @command="handleUserCommand">
              <span class="user-info">
                <el-avatar :size="28" style="background: linear-gradient(135deg, #409EFF, #67C23A);">
                  {{ user?.username?.charAt(0)?.toUpperCase() || 'U' }}
                </el-avatar>
                <span>{{ user?.username || '用户' }}</span>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon> 个人中心
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon> 退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <el-main class="main">
          <router-view v-slot="{ Component, route }">
            <transition name="fade" mode="out-in">
              <component :is="Component" :key="route.path" />
            </transition>
          </router-view>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)
const isFullscreen = ref(false)

const fullscreenRoutes = ['/chain-connect']

const user = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}')
  } catch {
    return null
  }
})

const activeMenu = computed(() => route.path)
const currentRoute = computed(() => route)

const showFullscreenToggle = computed(() => {
  return fullscreenRoutes.some(r => route.path.startsWith(r))
})

watch(() => route.path, (newPath) => {
  if (!fullscreenRoutes.some(r => newPath.startsWith(r))) {
    isFullscreen.value = false
  }
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  
  if (isFullscreen.value) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
}

function handleUserCommand(command) {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }
}
</script>

<style scoped>
.layout-wrapper {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.layout-wrapper.fullscreen-mode {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background: #fff;
}

.layout-container {
  height: 100vh;
}

.aside {
  background: linear-gradient(180deg, #1d3557 0%, #457b9d 100%);
  transition: width 0.3s ease;
  overflow-y: auto;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  white-space: nowrap;
}

.menu {
  border-right: none !important;
  background: transparent !important;
}

.menu :deep(.el-menu--popup) {
  background: linear-gradient(180deg, #1d3557 0%, #457b9d 100%) !important;
  border: none !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
}

.menu :deep(.el-sub-menu .el-menu) {
  background: transparent !important;
}

.menu :deep(.el-menu-item) {
  color: rgba(255, 255, 255, 0.8) !important;
  height: 50px;
  line-height: 50px;
  margin: 2px 6px;
  border-radius: 8px;
}

.menu :deep(.el-menu-item:hover),
.menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.15) !important;
  color: #fff !important;
}

.menu :deep(.el-sub-menu__title) {
  color: rgba(255, 255, 255, 0.8) !important;
  height: 50px;
  line-height: 50px;
  margin: 2px 6px;
  border-radius: 8px;
}

.menu :deep(.el-sub-menu .el-menu-item) {
  color: #fff !important;
  background: rgba(255, 255, 255, 0.12) !important;
  height: 44px;
  line-height: 44px;
  margin: 1px 12px;
  border-radius: 6px;
  min-width: auto;
}

.menu :deep(.el-sub-menu .el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.25) !important;
  color: #fff !important;
}

.menu :deep(.el-sub-menu .el-menu-item.is-active) {
  background: rgba(64, 158, 255, 0.8) !important;
  color: #fff !important;
}

.header {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 56px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
}

.collapse-btn:hover {
  color: #409eff;
  background: #f5f7fa;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 20px;
}

.user-info:hover {
  background: #f5f7fa;
}

.main {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
