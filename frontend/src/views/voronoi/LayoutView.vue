<template>
  <div class="layout-container">
    <aside class="layout-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-logo">
        <div class="logo-icon">
          <el-icon><PieChart /></el-icon>
        </div>
        <span class="logo-text">Voronoi 可视化</span>
      </div>
      <div class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
        <el-icon v-if="sidebarCollapsed"><ArrowRight /></el-icon>
        <el-icon v-else><ArrowLeft /></el-icon>
      </div>
      <el-menu :default-active="activeMenu" router background-color="transparent" text-color="#94a3b8"
               active-text-color="#fff" style="border:none">
        <el-menu-item index="/">
          <el-icon><DataBoard /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/datasets">
          <el-icon><FolderOpened /></el-icon>
          <span>数据管理</span>
        </el-menu-item>
        <el-menu-item index="/visualization">
          <el-icon><PieChart /></el-icon>
          <span>可视化展示</span>
        </el-menu-item>
        <el-menu-item index="/analysis">
          <el-icon><TrendCharts /></el-icon>
          <span>降维分析</span>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><UserFilled /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <div class="layout-main">
      <header class="layout-header">
        <div class="header-left">{{ pageTitle }}</div>
        <div class="header-right">
          <span class="header-username">{{ authStore.username }}</span>
          <el-button text type="danger" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon> 退出
          </el-button>
        </div>
      </header>
      <main class="layout-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/voronoi/auth'
import { DataBoard, FolderOpened, PieChart, SwitchButton, UserFilled, TrendCharts, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

const sidebarCollapsed = ref(false)

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  if (route.path.startsWith('/visualization')) return '/visualization'
  if (route.path.startsWith('/datasets')) return '/datasets'
  if (route.path.startsWith('/analysis')) return '/analysis'
  if (route.path.startsWith('/profile')) return '/profile'
  return '/'
})

const titleMap = {
  '/profile': '个人中心',
  '/analysis': '降维分析',
  '/visualization': '可视化展示',
  '/datasets': '数据管理',
  '/': '仪表盘',
}
const pageTitle = computed(() => {
  for (const [prefix, title] of Object.entries(titleMap)) {
    if (route.path === prefix || route.path.startsWith(prefix + '/')) return title
  }
  return 'Voronoi 可视化系统'
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>
