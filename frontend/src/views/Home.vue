<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="hero-section">
          <h1>综合可视化平台</h1>
          <p class="subtitle">通用多源数据可视化与分析工具</p>
          <p class="description">
            支持关系网络、层次数据、高维数据和空间分布等多种数据类型，
            提供数据源管理、数据处理、交互式可视化、统计分析和结果导出能力。
            新能源汽车电池健康与充电风险分析是本平台当前重点应用案例之一。
          </p>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="module-cards">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="module in modules" :key="module.name">
        <el-card shadow="hover" class="module-card" @click="$router.push(module.path)">
          <template #header>
            <div class="card-header">
              <el-icon :size="32" :color="module.color"><component :is="module.icon" /></el-icon>
              <span>{{ module.name }}</span>
            </div>
          </template>
          <p>{{ module.description }}</p>
          <el-button type="primary" link>进入模块 →</el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-divider />

    <el-row :gutter="20">
      <el-col :span="24">
        <div class="info-section">
          <h3>技术栈</h3>
          <el-tag v-for="tech in techs" :key="tech" style="margin: 4px;">{{ tech }}</el-tag>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { Share, DataLine, Histogram, Grid } from '@element-plus/icons-vue'

const modules = [
  {
    name: '新能源汽车电池分析案例',
    icon: 'Histogram',
    color: '#238A8D',
    path: '/ev-insight/health',
    description: '重点应用案例：分析车辆、电池、充电和故障数据，评估健康状态与充电风险。'
  },
  {
    name: '关系网络分析',
    icon: 'Share',
    color: '#409EFF',
    path: '/chain-connect',
    description: '导入节点与边数据，探索人物、组织、供应链或车辆之间的关系。'
  },
  {
    name: '数据流画布',
    icon: 'DataLine',
    color: '#67C23A',
    path: '/dataflow',
    description: '通过可视化画布组织数据处理流程，支持层次数据展示和分析大屏构建。'
  },
  {
    name: '高维数据分析',
    icon: 'Histogram',
    color: '#E6A23C',
    path: '/region',
    description: '对多维数据进行降维、聚类、区域划分和对比分析，发现数据中的模式。'
  },
  {
    name: 'Voronoi空间分析',
    icon: 'Grid',
    color: '#F56C6C',
    path: '/voronoi/analysis',
    description: '利用Voronoi分区和层次结构展示数据分布，支持多种交互式图表分析。'
  }
]

const techs = ['Vue 3', 'Vite', 'Element Plus', 'Pinia', 'ECharts', 'D3.js', 'Flask']
</script>

<style scoped>
.home {
  padding: 40px;
}

.hero-section {
  text-align: center;
  padding: 60px 0;
}

.hero-section h1 {
  font-size: 42px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: 20px;
  color: #606266;
  margin-bottom: 12px;
}

.description {
  font-size: 14px;
  color: #909399;
  max-width: 800px;
  margin: 0 auto;
  line-height: 1.8;
}

.module-cards {
  margin-top: 40px;
}

.module-card {
  cursor: pointer;
  transition: transform 0.3s ease;
  height: 100%;
}

.module-card:hover {
  transform: translateY(-5px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
}

.info-section {
  padding: 20px 0;
}

.info-section h3 {
  margin-bottom: 16px;
}
</style>
