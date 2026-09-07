<template>
  <div>
    <!-- 3 列可拖拽网格 -->
    <div class="dash-grid">
      <div
        v-for="(w, idx) in widgets"
        :key="w.id"
        class="dash-cell"
        :class="[
          w.span || '',
          { dragging: dragIdx === idx, 'drag-over': overIdx === idx }
        ]"
        draggable="true"
        @dragstart="onDragStart(idx, $event)"
        @dragover.prevent="onDragOver(idx)"
        @dragleave="overIdx = null"
        @drop="onDrop(idx)"
        @dragend="onDragEnd"
      >
        <!-- 欢迎横幅 -->
        <div v-if="w.type === 'welcome'" class="dashboard-welcome">
          <div class="cell-drag-badge">⠿</div>
          <h2>欢迎回来，Voronoi 可视化工作台</h2>
          <p>管理层次数据集，生成精美的 Voronoi 树图。所有卡片均可拖拽调整位置。</p>
        </div>

        <!-- 数据概览 -->
        <el-card v-else-if="w.type === 'stats'" shadow="never" class="h-full">
          <template #header>
            <div class="cell-header">
              <span class="cell-title">数据概览</span>
              <span class="cell-drag-badge">⠿</span>
            </div>
          </template>
          <div class="mini-stats">
            <div class="mini-stat" v-for="s in statCards" :key="s.key">
              <div class="mini-stat-icon" :style="{ background: s.gradient }">
                <el-icon :size="18"><component :is="s.icon" /></el-icon>
              </div>
              <div>
                <div class="mini-stat-val">{{ s.value }}</div>
                <div class="mini-stat-label">{{ s.label }}</div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 快捷操作 -->
        <el-card v-else-if="w.type === 'quick'" shadow="never" class="h-full">
          <template #header>
            <div class="cell-header">
              <span class="cell-title">快捷操作</span>
              <span class="cell-drag-badge">⠿</span>
            </div>
          </template>
          <div class="quick-grid">
            <div class="quick-item" @click="$router.push('/voronoi/data')">
              <div class="quick-icon" style="background:linear-gradient(135deg,#6366f1,#8b5cf6)">
                <el-icon :size="22"><UploadFilled /></el-icon>
              </div>
              <span>上传数据集</span>
            </div>
            <div class="quick-item" @click="$router.push('/voronoi/visualization')">
              <div class="quick-icon" style="background:linear-gradient(135deg,#22c55e,#16a34a)">
                <el-icon :size="22"><PieChart /></el-icon>
              </div>
              <span>可视化展示</span>
            </div>
            <div class="quick-item" @click="$router.push('/voronoi/analysis')">
              <div class="quick-icon" style="background:linear-gradient(135deg,#f59e0b,#d97706)">
                <el-icon :size="22"><TrendCharts /></el-icon>
              </div>
              <span>降维分析</span>
            </div>
            <div class="quick-item" @click="$router.push('/voronoi/profile')">
              <div class="quick-icon" style="background:linear-gradient(135deg,#ec4899,#be185d)">
                <el-icon :size="22"><UserFilled /></el-icon>
              </div>
              <span>个人中心</span>
            </div>
          </div>
        </el-card>

        <!-- 图表类型 -->
        <el-card v-else-if="w.type === 'charts'" shadow="never" class="h-full">
          <template #header>
            <div class="cell-header">
              <span class="cell-title">可视化类型</span>
              <span class="cell-drag-badge">⠿</span>
            </div>
          </template>
          <div class="chart-type-list">
            <div class="chart-type-row" v-for="ct in chartTypes" :key="ct.name"
                 @click="$router.push('/voronoi/visualization')">
              <span class="chart-type-dot" :style="{ background: ct.color }"></span>
              <span class="chart-type-name">{{ ct.name }}</span>
              <span class="chart-type-desc">{{ ct.desc }}</span>
            </div>
          </div>
        </el-card>

        <!-- 最近数据集 -->
        <el-card v-else-if="w.type === 'recent'" shadow="never">
          <template #header>
            <div class="cell-header">
              <span class="cell-title">最近上传</span>
              <div style="display:flex;align-items:center;gap:8px">
                <span class="cell-drag-badge">⠿</span>
                <el-button text type="primary" size="small" @click="$router.push('/voronoi/data')">查看全部</el-button>
              </div>
            </div>
          </template>
          <el-table :data="recentDatasets" stripe style="width:100%" v-loading="loading" size="small">
            <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
            <el-table-column prop="node_count" label="节点" width="70" align="center" />
            <el-table-column prop="max_depth" label="深度" width="60" align="center" />
            <el-table-column prop="leaf_count" label="叶节点" width="70" align="center" />
            <el-table-column label="操作" width="80" align="center">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="$router.push(`/voronoi/visualization/${row.id}`)">可视化</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loading && recentDatasets.length === 0" description="暂无数据集" :image-size="60">
            <el-button type="primary" size="small" @click="$router.push('/voronoi/data')">上传</el-button>
          </el-empty>
        </el-card>

        <!-- 使用提示 -->
        <el-card v-else-if="w.type === 'tips'" shadow="never" class="h-full">
          <template #header>
            <div class="cell-header">
              <span class="cell-title">使用提示</span>
              <span class="cell-drag-badge">⠿</span>
            </div>
          </template>
          <ul class="tips-list">
            <li>上传 <b>.json</b> 格式的层次数据文件即可开始可视化</li>
            <li>所有图表支持<b>鼠标滚轮缩放</b>和<b>拖拽平移</b></li>
            <li>力导向树中可直接<b>拖拽节点</b>调整位置</li>
            <li>可将聚类分析结果<b>保存为新数据集</b>直接可视化</li>
            <li>导出 <b>PNG / SVG</b> 格式的高清矢量图</li>
          </ul>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getDatasets } from '../../api/voronoi/dataset'
import { FolderOpened, Connection, TrendCharts, DataLine, UploadFilled, PieChart, UserFilled } from '@element-plus/icons-vue'

const loading = ref(true)
const allItems = ref([])
const totalCount = ref(0)

onMounted(async () => {
  try {
    const res = await getDatasets({ page: 1, per_page: 100 })
    allItems.value = res.data.items
    totalCount.value = res.data.total
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
})

const recentDatasets = computed(() => allItems.value.slice(0, 5))

const stats = computed(() => {
  const list = allItems.value
  return {
    total: totalCount.value,
    totalNodes: list.reduce((s, d) => s + (d.node_count || 0), 0),
    maxDepth: list.length ? Math.max(...list.map((d) => d.max_depth || 0)) : 0,
    totalLeaves: list.reduce((s, d) => s + (d.leaf_count || 0), 0),
  }
})

const statCards = computed(() => [
  { key: 'total', icon: 'FolderOpened', gradient: 'linear-gradient(135deg,#6366f1,#8b5cf6)', value: stats.value.total, label: '数据集' },
  { key: 'nodes', icon: 'Connection', gradient: 'linear-gradient(135deg,#22c55e,#16a34a)', value: stats.value.totalNodes, label: '节点' },
  { key: 'depth', icon: 'TrendCharts', gradient: 'linear-gradient(135deg,#f59e0b,#ea580c)', value: stats.value.maxDepth, label: '最大深度' },
  { key: 'leaves', icon: 'DataLine', gradient: 'linear-gradient(135deg,#06b6d4,#0284c7)', value: stats.value.totalLeaves, label: '叶节点' },
])

const chartTypes = [
  { name: 'Voronoi 树图', desc: '加权多边形空间填充', color: '#6366f1' },
  { name: '旭日图', desc: '径向层次分区', color: '#22c55e' },
  { name: '矩形树图', desc: '嵌套矩形面积映射', color: '#f59e0b' },
  { name: '冰柱图', desc: '垂直分区层次图', color: '#06b6d4' },
  { name: '力导向树', desc: '物理模拟节点布局', color: '#ec4899' },
]

const widgets = ref([
  { id: 'welcome', type: 'welcome', span: 'span-2' },
  { id: 'stats',   type: 'stats',   span: '' },
  { id: 'recent',  type: 'recent',  span: '' },
  { id: 'charts',  type: 'charts',  span: '' },
  { id: 'quick',   type: 'quick',   span: '' },
  { id: 'tips',    type: 'tips',    span: 'span-2' },
])

const dragIdx = ref(null)
const overIdx = ref(null)

function onDragStart(idx, e) {
  dragIdx.value = idx
  e.dataTransfer.effectAllowed = 'move'
}
function onDragOver(idx) {
  overIdx.value = idx
}
function onDrop(idx) {
  if (dragIdx.value !== null && dragIdx.value !== idx) {
    const arr = [...widgets.value]
    const [moved] = arr.splice(dragIdx.value, 1)
    arr.splice(idx, 0, moved)
    widgets.value = arr
  }
  overIdx.value = null
}
function onDragEnd() {
  dragIdx.value = null
  overIdx.value = null
}
</script>
