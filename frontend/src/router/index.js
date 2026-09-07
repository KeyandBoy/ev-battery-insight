import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/common/Layout.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    redirect: '/home',
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { title: '首页' }
      },
      
      // ===== Chain-Connect 模块（支持全屏）=====
      {
        path: 'chain-connect',
        name: 'ChainConnect',
        component: () => import('@/views/chain-connect/Dashboard.vue'),
        meta: { title: '图神经网络可视化', fullscreen: true }
      },
      
      // ===== DataFlow 模块（孙思玉）=====
      {
        path: 'dataflow',
        name: 'DataFlowHome',
        component: () => import('@/views/dataflow/HomeView.vue'),
        meta: { title: '数据流画布', subtitle: '基于正方化算法的层次数据可视化' }
      },
      {
        path: 'dataflow/editor',
        name: 'DashboardEditor',
        component: () => import('@/views/dataflow/DashboardEditorView.vue'),
        meta: { title: '大屏编辑器' }
      },
      {
        path: 'dataflow/datasets',
        name: 'DatasetManager',
        component: () => import('@/views/dataflow/DatasetView.vue'),
        meta: { title: '数据集管理' }
      },
      {
        path: 'dataflow/treemap',
        name: 'TreemapAnalysis',
        component: () => import('@/views/dataflow/TreemapView.vue'),
        meta: { title: 'Treemap分析' }
      },
      {
        path: 'dataflow/profile',
        name: 'DataFlowProfile',
        component: () => import('@/views/dataflow/ProfileView.vue'),
        meta: { title: '个人资料' }
      },
      
      // ===== Region 模块（岳浩然）=====
      {
        path: 'region',
        name: 'RegionStudio',
        component: () => import('@/views/region/StudioView.vue'),
        meta: { title: '高维区域可视化工作台', glassStyle: true }
      },
      {
        path: 'region/dashboard',
        name: 'RegionDashboard',
        component: () => import('@/views/region/DashboardView.vue'),
        meta: { title: '控制台' }
      },
      {
        path: 'region/experiment',
        name: 'RegionExperiment',
        component: () => import('@/views/region/ExperimentView.vue'),
        meta: { title: '对比实验' }
      },
      
      // ===== Voronoi 模块（朱娜）=====
      {
        path: 'voronoi/analysis',
        name: 'VoronoiAnalysis',
        component: () => import('@/views/voronoi/AnalysisView.vue'),
        meta: { title: '数据分析' }
      },
      {
        path: 'voronoi/dashboard',
        name: 'VoronoiDashboard',
        component: () => import('@/views/voronoi/DashboardView.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'voronoi/data',
        name: 'VoronoiDataManager',
        component: () => import('@/views/voronoi/DataManagerView.vue'),
        meta: { title: '数据管理' }
      },
      {
        path: 'voronoi/visualization',
        name: 'VoronoiVisualization',
        component: () => import('@/views/voronoi/VisualizationView.vue'),
        meta: { title: '可视化展示' }
      },
      {
        path: 'voronoi/profile',
        name: 'VoronoiProfile',
        component: () => import('@/views/voronoi/ProfileView.vue'),
        meta: { title: '个人资料' }
      }
    ]
  },
  
  // ===== 认证页面 =====
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/chain-connect/Register.vue'),
    meta: { title: '注册' }
  },
  
  // ===== 404 =====
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '404' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    return { top: 0 }
  }
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 综合可视化平台` : '综合可视化平台'
  
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token && !['/register'].includes(to.path)) {
    next('/login?redirect=' + to.fullPath)
  } else {
    next()
  }
})

export default router
