<template>
  <main class="center-canvas">
    <!-- 工具栏 -->
    <div class="canvas-toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="graphStore.searchKeyword"
          placeholder="搜索节点..."
          prefix-icon="Search"
          size="small"
          clearable
          style="width: 200px;"
        />
        <el-select
          v-model="graphStore.selectedCategories"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="筛选分类"
          size="small"
          clearable
          style="width: 200px;"
        >
          <el-option
            v-for="(cat, idx) in graphStore.graphData.categories"
            :key="idx"
            :label="cat.name"
            :value="idx"
          />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-tooltip content="重置缩放" placement="bottom">
          <el-button size="small" :icon="RefreshRight" circle @click="handleResetZoom" />
        </el-tooltip>
        <el-tooltip content="全屏" placement="bottom">
          <el-button size="small" :icon="FullScreen" circle @click="toggleFullscreen" />
        </el-tooltip>
        <el-tooltip content="导出图片" placement="bottom">
          <el-button size="small" :icon="Download" circle @click="handleExportImage" />
        </el-tooltip>
      </div>
    </div>

    <!-- 图表容器 -->
    <div class="chart-wrapper" ref="chartWrapperRef">
      <div ref="chartRef" class="chart-container"></div>

      <!-- 空状态 -->
      <div v-if="!hasData" class="empty-state">
        <el-empty description="暂无图数据">
          <template #image>
            <el-icon :size="80" color="#c0c4cc"><Share /></el-icon>
          </template>
          <p class="empty-hint">请从右侧面板选择数据集或导入数据</p>
        </el-empty>
      </div>
    </div>

    <!-- 底部信息栏 -->
    <div class="canvas-footer">
      <div class="footer-left">
        <el-tag size="small" type="info">节点: {{ graphStore.nodeCount }}</el-tag>
        <el-tag size="small" type="info">边: {{ graphStore.linkCount }}</el-tag>
        <el-tag size="small" type="success">{{ layoutLabel }}</el-tag>
        <el-tag v-if="graphStore.dataSource.name" size="small">{{ graphStore.dataSource.name }}</el-tag>
      </div>
      <div class="footer-right">
        <span class="zoom-info">缩放: {{ zoomLevel }}%</span>
      </div>
    </div>
  </main>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick, markRaw } from 'vue'
import * as echarts from 'echarts'
import { RefreshRight, FullScreen, Download } from '@element-plus/icons-vue'
import { useGraphStore } from '../../stores/chain-connect/graph'
import { ElMessage } from 'element-plus'

const graphStore = useGraphStore()
const chartRef = ref(null)
const chartWrapperRef = ref(null)
let chart = null
const zoomLevel = ref(100)

const hasData = computed(() => graphStore.graphData.nodes.length > 0)

const layoutLabel = computed(() => {
  const map = {
    force: '力导向布局',
    circular: '环形布局',
    grid: '网格布局',
    tree: '层次布局'
  }
  return map[graphStore.layoutType] || '力导向布局'
})

// 颜色方案
const colorPalette = [
  '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
  '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#48b0d6',
  '#ff9f7f', '#8d98b3', '#e7bcf3', '#fb7293', '#bda29a'
]

function getFilteredData() {
  const { nodes, links, categories } = graphStore.graphData
  const keyword = graphStore.searchKeyword.toLowerCase()
  const selectedCats = graphStore.selectedCategories

  let filteredNodes = nodes
  if (keyword) {
    filteredNodes = filteredNodes.filter(n =>
      n.name.toLowerCase().includes(keyword) || (n.desc && n.desc.toLowerCase().includes(keyword))
    )
  }
  if (selectedCats.length > 0) {
    filteredNodes = filteredNodes.filter(n => selectedCats.includes(n.category))
  }

  const nodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredLinks = links.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target))

  return { nodes: filteredNodes, links: filteredLinks, categories }
}

function buildChartOption() {
  const filtered = getFilteredData()
  const nodes = filtered.nodes.map(n => ({ ...n }))
  const links = filtered.links
  const categories = filtered.categories
  const vc = graphStore.visualConfig
  const lt = graphStore.layoutType

  if (nodes.length === 0) return null

  // 构建布局配置
  let layoutOpt = {}
  if (lt === 'force') {
    const fc = graphStore.layoutConfig.force
    layoutOpt = {
      layout: 'force',
      force: {
        repulsion: fc.repulsion,
        gravity: fc.gravity,
        edgeLength: fc.edgeLength,
        friction: fc.friction,
        layoutAnimation: true
      }
    }
  } else if (lt === 'circular') {
    layoutOpt = {
      layout: 'circular',
      circular: {
        rotateLabel: true
      }
    }
  } else if (lt === 'grid') {
    // ECharts没有原生grid布局，手动计算位置
    const cols = Math.ceil(Math.sqrt(nodes.length))
    const spacing = 80
    nodes.forEach((node, i) => {
      node.x = (i % cols) * spacing
      node.y = Math.floor(i / cols) * spacing
      node.fixed = true
    })
    layoutOpt = { layout: 'none' }
  } else if (lt === 'tree') {
    // 模拟层次布局：通过入度判断层级
    const inDegree = {}
    nodes.forEach(n => { inDegree[n.id] = 0 })
    links.forEach(l => {
      if (inDegree[l.target] !== undefined) {
        inDegree[l.target] = (inDegree[l.target] || 0) + 1
      }
    })
    // 拓扑排序确定层级
    const layers = {}
    const visited = new Set()
    const queue = []
    nodes.forEach(n => {
      if (inDegree[n.id] === 0) {
        queue.push(n.id)
        layers[n.id] = 0
      }
    })
    if (queue.length === 0 && nodes.length > 0) {
      queue.push(nodes[0].id)
      layers[nodes[0].id] = 0
    }
    while (queue.length > 0) {
      const curr = queue.shift()
      visited.add(curr)
      links.forEach(l => {
        if (l.source === curr && !visited.has(l.target)) {
          layers[l.target] = (layers[curr] || 0) + 1
          queue.push(l.target)
          visited.add(l.target)
        }
      })
    }
    // 未访问到的节点放最后一层
    const maxLayer = Math.max(...Object.values(layers), 0)
    nodes.forEach(n => {
      if (layers[n.id] === undefined) {
        layers[n.id] = maxLayer + 1
      }
    })
    // 按层排列
    const layerNodes = {}
    nodes.forEach(n => {
      const ly = layers[n.id] || 0
      if (!layerNodes[ly]) layerNodes[ly] = []
      layerNodes[ly].push(n)
    })
    const layerSpacingY = 120
    const nodeSpacingX = 100
    Object.keys(layerNodes).forEach(layer => {
      const nodesInLayer = layerNodes[layer]
      const startX = -(nodesInLayer.length - 1) * nodeSpacingX / 2
      nodesInLayer.forEach((n, i) => {
        n.x = startX + i * nodeSpacingX
        n.y = parseInt(layer) * layerSpacingY
        n.fixed = true
      })
    })
    layoutOpt = { layout: 'none' }
  }

  // 计算节点大小范围
  const values = nodes.map(n => n.value || 1)
  const minVal = Math.min(...values)
  const maxVal = Math.max(...values)

  const seriesData = nodes.map(n => {
    let size = vc.nodeSize
    if (vc.nodeSizeByValue && maxVal > minVal) {
      size = 15 + ((n.value - minVal) / (maxVal - minVal)) * (vc.nodeSize * 1.5)
    }
    const item = {
      id: n.id,
      name: n.name,
      value: n.value,
      category: n.category,
      symbolSize: size,
      desc: n.desc || '',
      label: {
        show: vc.labelShow,
        fontSize: vc.labelFontSize,
        color: '#333'
      }
    }
    if (n.x !== undefined) item.x = n.x
    if (n.y !== undefined) item.y = n.y
    if (n.fixed) item.fixed = true
    return item
  })

  const seriesLinks = links.map(l => ({
    source: l.source,
    target: l.target,
    value: l.value,
    relation: l.relation || '',
    lineStyle: {
      width: vc.edgeWidthByValue ? Math.max(0.5, (l.value || 1) * vc.edgeWidth / 5) : vc.edgeWidth,
      curveness: vc.edgeCurveness,
      color: '#adb5bd'
    },
    label: {
      show: vc.edgeLabelShow,
      formatter: l.relation || '',
      fontSize: 10,
      color: '#999'
    }
  }))

  const cats = (categories || []).map((c, i) => ({
    name: c.name,
    itemStyle: {
      color: colorPalette[i % colorPalette.length]
    }
  }))

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'node') {
          const d = params.data
          return `<div style="font-weight:bold;margin-bottom:4px;">${d.name}</div>
                  <div>权重: ${d.value || '-'}</div>
                  <div>分类: ${cats[d.category]?.name || '-'}</div>
                  <div>${d.desc || ''}</div>`
        } else if (params.dataType === 'edge') {
          const d = params.data
          return `<div>${d.source} → ${d.target}</div>
                  <div>关系: ${d.relation || '-'}</div>
                  <div>权重: ${d.value || '-'}</div>`
        }
        return ''
      },
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e4e7ed',
      textStyle: { color: '#303133', fontSize: 13 },
      padding: [10, 14],
      extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 8px;'
    },
    legend: {
      data: cats.map(c => c.name),
      orient: 'horizontal',
      bottom: 10,
      textStyle: { fontSize: 12 },
      icon: 'circle',
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 16
    },
    animationDuration: 800,
    animationEasingUpdate: 'quinticInOut',
    series: [{
      type: 'graph',
      ...layoutOpt,
      data: seriesData,
      links: seriesLinks,
      categories: cats,
      roam: true,
      draggable: true,
      symbol: vc.symbolType,
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: [0, 8],
      emphasis: {
        focus: 'adjacency',
        blurScope: 'coordinateSystem',
        lineStyle: { width: 4 },
        itemStyle: {
          shadowBlur: 20,
          shadowColor: 'rgba(0,0,0,0.3)'
        }
      },
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 2,
        shadowBlur: 8,
        shadowColor: 'rgba(0,0,0,0.1)'
      },
      lineStyle: {
        opacity: 0.7
      },
      scaleLimit: {
        min: 0.2,
        max: 5
      }
    }]
  }
}

function renderChart() {
  if (!chart || !chartRef.value) return
  const option = buildChartOption()
  if (option) {
    chart.clear()
    chart.setOption(option, true)
  } else {
    chart.clear()
  }
}

function handleResetZoom() {
  if (chart) {
    chart.dispatchAction({ type: 'restore' })
    zoomLevel.value = 100
  }
}

function toggleFullscreen() {
  const wrapper = chartWrapperRef.value
  if (!wrapper) return
  if (!document.fullscreenElement) {
    wrapper.requestFullscreen?.()
  } else {
    document.exitFullscreen?.()
  }
}

function handleExportImage() {
  if (!chart) return
  const url = chart.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff'
  })
  const link = document.createElement('a')
  link.download = `network-graph-${Date.now()}.png`
  link.href = url
  link.click()
  ElMessage.success('图片已导出')
}

// 监听数据和配置变化
watch(
  () => [
    graphStore.graphData,
    graphStore.layoutType,
    graphStore.layoutConfig,
    graphStore.visualConfig,
    graphStore.searchKeyword,
    graphStore.selectedCategories
  ],
  () => {
    nextTick(() => renderChart())
  },
  { deep: true }
)

let resizeObserver = null

onMounted(() => {
  chart = markRaw(echarts.init(chartRef.value, null, { renderer: 'canvas' }))

  chart.on('graphRoam', (params) => {
    if (params.zoom) {
      zoomLevel.value = Math.round(zoomLevel.value * params.zoom)
    }
  })

  resizeObserver = new ResizeObserver(() => {
    chart?.resize()
  })
  resizeObserver.observe(chartRef.value)

  renderChart()
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chart?.dispose()
})
</script>

<style scoped>
.center-canvas {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #fafbfc;
}

.canvas-toolbar {
  height: 44px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chart-wrapper {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.chart-container {
  width: 100%;
  height: 100%;
}

.empty-state {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(250, 251, 252, 0.9);
}

.empty-hint {
  color: #909399;
  font-size: 14px;
  margin-top: 8px;
}

.canvas-footer {
  height: 32px;
  background: #fff;
  border-top: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
}

.footer-left {
  display: flex;
  gap: 6px;
}

.footer-right {
  font-size: 12px;
  color: #909399;
}

.zoom-info {
  font-family: 'Courier New', monospace;
}
</style>
