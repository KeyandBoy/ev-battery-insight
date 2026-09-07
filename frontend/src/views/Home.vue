<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="hero-section">
          <h1>综合可视化平台</h1>
          <p class="subtitle">集成四大可视化模块的一体化分析系统</p>
          <p class="description">
            本平台整合了 DataFlow（数据流画布）、Region（高维区域可视化）、
            Voronoi（Voronoi图分析）和 Chain-Connect（图神经网络可视化）
            四个独立项目，提供统一的访问入口和一致的用户体验。
          </p>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="module-cards">
      <el-col :span="6" v-for="module in modules" :key="module.name">
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
    name: '新能源汽车电池分析',
    icon: 'Histogram',
    color: '#238A8D',
    path: '/ev-insight/health',
    description: 'EV-Battery Insight，分析车辆电池健康状态与充电风险'
  },
  {
    name: '图神经网络可视化',
    icon: 'Share',
    color: '#409EFF',
    path: '/chain-connect',
    description: 'Chain-Connect模块，基于图神经网络的社交网络数据可视化'
  },
  {
    name: '数据流画布',
    icon: 'DataLine',
    color: '#67C23A',
    path: '/dataflow',
    description: 'DataFlow模块，基于正方化算法的层次数据可视化构件系统'
  },
  {
    name: '高维区域可视化',
    icon: 'Histogram',
    color: '#E6A23C',
    path: '/region',
    description: 'Region模块，高维数据的区域划分与可视化分析'
  },
  {
    name: 'Voronoi图分析',
    icon: 'Grid',
    color: '#F56C6C',
    path: '/voronoi/analysis',
    description: 'Voronoi模块，基于Voronoi图的层次数据可视化与分析'
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
