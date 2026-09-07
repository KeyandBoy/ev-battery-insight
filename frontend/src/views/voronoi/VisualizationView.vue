<template>
  <div class="vis-page" :class="{ 'vis-fullscreen': isFullscreen }" ref="visContainerRef">
    <!-- ===== 左侧主区域 ===== -->
    <div class="vis-main">
      <!-- 顶部工具条 -->
      <div class="vis-toolbar">
        <el-tag v-if="datasetStore.currentDataset" type="info" effect="plain" class="vis-meta-tag">
          <span>{{ datasetStore.currentDataset.name }}</span>
          <span class="divider">|</span>
          <span>{{ datasetStore.currentDataset.node_count }} 节点</span>
          <span class="divider">|</span>
          <span>深度 {{ datasetStore.currentDataset.max_depth }}</span>
        </el-tag>
        <div style="flex:1" />
        <el-input v-if="chartType === 'voronoi'" v-model="searchQuery" placeholder="搜索节点..."
                  clearable style="width:150px" size="small" :prefix-icon="Search" />
        <el-button-group>
          <el-tooltip content="重置缩放" placement="bottom">
            <el-button :icon="RefreshRight" size="small" @click="handleResetZoom" />
          </el-tooltip>
          <el-tooltip content="导出 PNG" placement="bottom">
            <el-button :icon="Picture" size="small" @click="exportPng" />
          </el-tooltip>
          <el-tooltip content="导出 SVG" placement="bottom">
            <el-button :icon="Download" size="small" @click="exportSvg" />
          </el-tooltip>
          <el-tooltip :content="isFullscreen ? '退出全屏' : '全屏'" placement="bottom">
            <el-button :icon="isFullscreen ? CloseBold : FullScreen" size="small" @click="toggleFullscreen" />
          </el-tooltip>
        </el-button-group>
      </div>

      <!-- 图表区域 / 拖拽放置区 -->
      <div class="vis-chart-wrapper" ref="chartWrapperRef"
           v-loading="datasetStore.loading" element-loading-text="正在加载数据..."
           @dragover.prevent="onDragOver"
           @dragleave="onDragLeave"
           @drop="onChartDrop"
           :class="{ 'drop-active': dropActive }">
        <template v-if="treeData">
          <VoronoiTreemap v-show="chartType === 'voronoi'" ref="voronoiRef"
            :data="treeData" :iterations="iterations" :padding="2.5"
            :render-key="renderKey" :color-scheme="colorScheme" :search-query="searchQuery" />
          <SunburstChart v-if="chartType === 'sunburst'" ref="sunburstRef"
            :data="treeData" :color-scheme="colorScheme" :render-key="renderKey" />
          <RectTreemap v-if="chartType === 'treemap'" ref="rectTreemapRef"
            :data="treeData" :color-scheme="colorScheme" :render-key="renderKey" />
          <IcicleChart v-if="chartType === 'icicle'" ref="icicleRef"
            :data="treeData" :color-scheme="colorScheme" :render-key="renderKey" />
          <ForceTree v-if="chartType === 'force'" ref="forceRef"
            :data="treeData" :color-scheme="colorScheme" :render-key="renderKey" />
        </template>
        <div v-else class="vis-drop-hint">
          <div class="drop-icon">📊</div>
          <p class="drop-title">将数据集拖拽到此处</p>
          <p class="drop-sub">从右侧面板拖入数据集、图表类型或配色方案</p>
        </div>
      </div>
    </div>

    <!-- ===== 右侧面板 ===== -->
    <div class="vis-panel" :class="{ collapsed: panelCollapsed }">
      <div class="vis-panel-toggle" @click="panelCollapsed = !panelCollapsed">
        <el-icon :size="14"><component :is="panelCollapsed ? 'ArrowLeft' : 'ArrowRight'" /></el-icon>
      </div>

      <div class="vis-panel-body" v-show="!panelCollapsed">
        <!-- 数据集列表 -->
        <div class="vp-section">
          <div class="vp-title">数据集</div>
          <el-input v-model="dsSearch" placeholder="搜索数据集..." size="small" clearable
                    style="margin-bottom:10px" :prefix-icon="Search" />
          <div class="vp-ds-list" v-loading="listLoading">
            <div v-for="ds in filteredDatasets" :key="ds.id"
                 class="vp-ds-item" :class="{ active: selectedId === ds.id }"
                 draggable="true"
                 @dragstart="onItemDragStart('dataset', String(ds.id), $event)">
              <div class="vp-ds-name">{{ ds.name }}</div>
              <div class="vp-ds-meta">
                <span>{{ ds.node_count }} 节点</span>
                <span>深度 {{ ds.max_depth }}</span>
              </div>
            </div>
            <div v-if="!listLoading && filteredDatasets.length === 0" class="vp-ds-empty">
              暂无数据集
            </div>
          </div>
        </div>

        <!-- 图表类型 -->
        <div class="vp-section">
          <div class="vp-title">图表类型</div>
          <div class="vp-ct-grid">
            <div v-for="ct in chartTypeOptions" :key="ct.value"
                 class="vp-ct-item" :class="{ active: chartType === ct.value }"
                 draggable="true"
                 @dragstart="onItemDragStart('chart', ct.value, $event)">
              <span class="vp-ct-dot" :style="{ background: ct.color }"></span>
              <span>{{ ct.label }}</span>
            </div>
          </div>
        </div>

        <!-- 配色方案 -->
        <div class="vp-section">
          <div class="vp-title">配色方案</div>
          <div class="vp-color-grid">
            <div v-for="cs in colorOptions" :key="cs.value"
                 class="vp-color-item" :class="{ active: colorScheme === cs.value }"
                 draggable="true"
                 @dragstart="onItemDragStart('color', cs.value, $event)">
              <div class="vp-color-dots">
                <span v-for="c in cs.preview" :key="c" :style="{ background: c }"></span>
              </div>
              <span>{{ cs.label }}</span>
            </div>
          </div>
        </div>

        <!-- Voronoi 参数 -->
        <div class="vp-section" v-if="chartType === 'voronoi'">
          <div class="vp-title">迭代次数 <span class="vp-title-val">{{ iterations }}</span></div>
          <el-slider v-model="iterations" :min="10" :max="200" :step="10" @change="recompute" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useDatasetStore } from '../../stores/voronoi/dataset'
import { getDatasets } from '../../api/voronoi/dataset'
import { ElMessage } from 'element-plus'
import { RefreshRight, Picture, Download, FullScreen, CloseBold, Search } from '@element-plus/icons-vue'
import VoronoiTreemap from '../../components/voronoi/VoronoiTreemap.vue'
import SunburstChart from '../../components/voronoi/SunburstChart.vue'
import RectTreemap from '../../components/voronoi/RectTreemap.vue'
import IcicleChart from '../../components/voronoi/IcicleChart.vue'
import ForceTree from '../../components/voronoi/ForceTree.vue'

const props = defineProps({ id: { type: [String, Number], default: null } })
const route = useRoute()
const datasetStore = useDatasetStore()

const voronoiRef = ref(null)
const sunburstRef = ref(null)
const rectTreemapRef = ref(null)
const icicleRef = ref(null)
const forceRef = ref(null)
const visContainerRef = ref(null)
const chartWrapperRef = ref(null)

const selectedId = ref(null)
const allDatasets = ref([])
const listLoading = ref(false)
const iterations = ref(60)
const renderKey = ref(0)
const colorScheme = ref('classic')
const searchQuery = ref('')
const isFullscreen = ref(false)
const chartType = ref('voronoi')
const panelCollapsed = ref(false)
const dsSearch = ref('')
const dropActive = ref(false)

const treeData = computed(() => datasetStore.currentTreeData)

const currentChartRef = computed(() => {
  const map = { voronoi: voronoiRef, sunburst: sunburstRef, treemap: rectTreemapRef, icicle: icicleRef, force: forceRef }
  return map[chartType.value]
})

const filteredDatasets = computed(() => {
  const q = dsSearch.value.trim().toLowerCase()
  if (!q) return allDatasets.value
  return allDatasets.value.filter(d => d.name.toLowerCase().includes(q))
})

const chartTypeOptions = [
  { value: 'voronoi',  label: 'Voronoi 树图', color: '#6366f1' },
  { value: 'sunburst', label: '旭日图',       color: '#22c55e' },
  { value: 'treemap',  label: '矩形树图',     color: '#f59e0b' },
  { value: 'icicle',   label: '冰柱图',       color: '#06b6d4' },
  { value: 'force',    label: '力导向树',     color: '#ec4899' },
]

const colorOptions = [
  { value: 'classic', label: '经典', preview: ['#4e79a7','#f28e2b','#e15759','#76b7b2'] },
  { value: 'ocean',   label: '海洋', preview: ['#264653','#2a9d8f','#e9c46a','#e76f51'] },
  { value: 'forest',  label: '森林', preview: ['#2d6a4f','#40916c','#52b788','#95d5b2'] },
  { value: 'sunset',  label: '日落', preview: ['#ff6b6b','#ee5a24','#ffa502','#f8a5c2'] },
  { value: 'tech',    label: '科技', preview: ['#00b4d8','#0077b6','#5e60ce','#7400b8'] },
]

onMounted(async () => {
  listLoading.value = true
  try {
    const res = await getDatasets({ per_page: 200 })
    allDatasets.value = res.data.items
  } catch {
    ElMessage.error('加载数据集列表失败')
  } finally {
    listLoading.value = false
  }

  const routeId = route.params.id || props.id
  if (routeId) {
    selectedId.value = Number(routeId)
    loadDataset(selectedId.value)
  }

  document.addEventListener('fullscreenchange', onFullscreenChange)
})

onBeforeUnmount(() => {
  datasetStore.resetVisualization()
  document.removeEventListener('fullscreenchange', onFullscreenChange)
})

watch(() => route.params.id, (newId) => {
  if (newId && Number(newId) !== selectedId.value) {
    selectedId.value = Number(newId)
    loadDataset(selectedId.value)
  }
})

async function loadDataset(id) {
  if (!id) return
  selectedId.value = id
  try {
    await datasetStore.fetchDatasetData(id)
  } catch (err) {
    ElMessage.error(err?.message || '加载数据失败')
  }
}

function recompute() { renderKey.value++ }

function handleResetZoom() {
  const refMap = { voronoi: voronoiRef, sunburst: sunburstRef, treemap: rectTreemapRef, icicle: icicleRef, force: forceRef }
  refMap[chartType.value]?.value?.resetZoom?.()
}

function onItemDragStart(type, value, e) {
  e.dataTransfer.setData('application/json', JSON.stringify({ type, value }))
  e.dataTransfer.effectAllowed = 'copy'
}

function onDragOver(e) {
  dropActive.value = true
  e.dataTransfer.dropEffect = 'copy'
}

function onDragLeave() {
  dropActive.value = false
}

function onChartDrop(e) {
  dropActive.value = false
  try {
    const payload = JSON.parse(e.dataTransfer.getData('application/json'))
    if (payload.type === 'dataset') loadDataset(Number(payload.value))
    else if (payload.type === 'chart') chartType.value = payload.value
    else if (payload.type === 'color') colorScheme.value = payload.value
  } catch { /* ignore */ }
}

function getActiveSvg() {
  return currentChartRef.value?.value?.getSvgElement?.() || null
}

function exportSvg() {
  const svgEl = getActiveSvg()
  if (!svgEl) { ElMessage.warning('请先加载可视化'); return }
  const clone = svgEl.cloneNode(true)
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  const svgString = new XMLSerializer().serializeToString(clone)
  downloadBlob(new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' }),
    `${chartType.value}_${selectedId.value || 'chart'}.svg`)
  ElMessage.success('SVG 已导出')
}

function exportPng() {
  const svgEl = getActiveSvg()
  if (!svgEl) { ElMessage.warning('请先加载可视化'); return }
  const clone = svgEl.cloneNode(true)
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  const svgString = new XMLSerializer().serializeToString(clone)
  const w = parseInt(svgEl.getAttribute('width')) || 800
  const h = parseInt(svgEl.getAttribute('height')) || 600
  const scale = 2
  const canvas = document.createElement('canvas')
  canvas.width = w * scale; canvas.height = h * scale
  const ctx = canvas.getContext('2d')
  ctx.scale(scale, scale)
  const img = new Image()
  img.onload = () => {
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, w, h)
    ctx.drawImage(img, 0, 0, w, h)
    canvas.toBlob((blob) => {
      if (blob) {
        downloadBlob(blob, `${chartType.value}_${selectedId.value || 'chart'}.png`)
        ElMessage.success('PNG 已导出 (2x 高清)')
      }
    }, 'image/png')
  }
  img.onerror = () => { ElMessage.error('PNG 导出失败') }
  img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgString)
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  URL.revokeObjectURL(url)
}

function toggleFullscreen() {
  const el = visContainerRef.value
  if (!el) return
  if (!document.fullscreenElement) {
    el.requestFullscreen().catch(() => { isFullscreen.value = false })
  } else {
    document.exitFullscreen()
  }
}

function onFullscreenChange() { isFullscreen.value = !!document.fullscreenElement }
</script>
