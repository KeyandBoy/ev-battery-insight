import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useGraphStore = defineStore('graph', () => {
  // 当前图数据
  const graphData = ref({ nodes: [], links: [], categories: [] })

  // 当前布局类型
  const layoutType = ref('force')

  // 当前数据来源信息
  const dataSource = ref({ type: '', name: '', description: '' })

  // 布局配置
  const layoutConfig = ref({
    force: {
      repulsion: 500,
      gravity: 0.1,
      edgeLength: 120,
      friction: 0.6
    },
    circular: {
      radius: null,
      rotateLabel: true
    },
    grid: {
      cols: 0
    }
  })

  // 视觉配置
  const visualConfig = ref({
    nodeSize: 30,
    nodeSizeByValue: true,
    labelShow: true,
    labelFontSize: 12,
    edgeWidth: 1.5,
    edgeWidthByValue: true,
    edgeLabelShow: true,
    edgeCurveness: 0.3,
    symbolType: 'circle',
    colorScheme: 'default'
  })

  // 搜索过滤
  const searchKeyword = ref('')
  const selectedCategories = ref([])

  // 统计信息
  const statsData = ref(null)

  // 计算属性
  const nodeCount = computed(() => graphData.value.nodes.length)
  const linkCount = computed(() => graphData.value.links.length)
  const categoryCount = computed(() => graphData.value.categories.length)

  function setGraphData(data) {
    graphData.value = data || { nodes: [], links: [], categories: [] }
    // 重置选中分类
    selectedCategories.value = []
    searchKeyword.value = ''
  }

  function setLayoutType(type) {
    layoutType.value = type
  }

  function setDataSource(source) {
    dataSource.value = source
  }

  function updateLayoutConfig(type, config) {
    if (layoutConfig.value[type]) {
      Object.assign(layoutConfig.value[type], config)
    }
  }

  function updateVisualConfig(config) {
    Object.assign(visualConfig.value, config)
  }

  function setStatsData(data) {
    statsData.value = data
  }

  return {
    graphData,
    layoutType,
    dataSource,
    layoutConfig,
    visualConfig,
    searchKeyword,
    selectedCategories,
    statsData,
    nodeCount,
    linkCount,
    categoryCount,
    setGraphData,
    setLayoutType,
    setDataSource,
    updateLayoutConfig,
    updateVisualConfig,
    setStatsData
  }
})
