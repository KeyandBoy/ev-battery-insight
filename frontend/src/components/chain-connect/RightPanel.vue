<template>
  <aside class="right-panel" :class="{ collapsed: isCollapsed }">
    <div class="panel-toggle" @click="isCollapsed = !isCollapsed">
      <el-icon :size="16">
        <component :is="isCollapsed ? 'Back' : 'Right'" />
      </el-icon>
    </div>

    <div v-show="!isCollapsed" class="panel-content">
      <el-tabs v-model="activeTab" class="panel-tabs">
        <!-- 数据来源 Tab -->
        <el-tab-pane label="数据来源" name="datasource">
          <div class="tab-section">
            <!-- 示例数据集 -->
            <div class="section-header">
              <el-icon><DataBoard /></el-icon>
              <span>示例数据集</span>
            </div>
            <div class="dataset-list">
              <div
                v-for="ds in datasets"
                :key="ds.id"
                class="dataset-card"
                :class="{ active: currentDatasetId === ds.id }"
                @click="loadDataset(ds)"
              >
                <div class="dataset-name">{{ ds.name }}</div>
                <div class="dataset-desc">{{ ds.description }}</div>
                <div class="dataset-meta">
                  <el-tag size="small" type="info">{{ ds.graph_data?.nodes?.length || 0 }}节点</el-tag>
                  <el-tag size="small" type="info">{{ ds.graph_data?.links?.length || 0 }}边</el-tag>
                </div>
              </div>
            </div>

            <el-divider />

            <!-- JSON导入 -->
            <div class="section-header">
              <el-icon><Upload /></el-icon>
              <span>导入数据</span>
            </div>
            <el-upload
              class="json-upload"
              action=""
              :auto-upload="false"
              accept=".json"
              :show-file-list="false"
              @change="handleFileUpload"
            >
              <el-button type="primary" plain size="small" style="width: 100%;">
                <el-icon><Upload /></el-icon> 上传 JSON 文件
              </el-button>
            </el-upload>

            <el-divider />

            <!-- 保存为项目 -->
            <div class="section-header">
              <el-icon><FolderAdd /></el-icon>
              <span>保存为项目</span>
            </div>
            <div class="save-form">
              <el-input
                v-model="saveProjectName"
                placeholder="项目名称"
                size="small"
              />
              <el-button
                type="success"
                size="small"
                :disabled="!graphStore.nodeCount || !saveProjectName"
                @click="handleSaveProject"
              >
                保存
              </el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- 文本提取 Tab -->
        <el-tab-pane label="文本提取" name="text">
          <div class="tab-section">
            <div class="section-header">
              <el-icon><EditPen /></el-icon>
              <span>输入文本内容</span>
            </div>
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="10"
              placeholder="请输入包含人物关系的文本内容，系统将自动提取人物关系并生成图谱。例如：&#10;&#10;张三和李四是大学同学，毕业后一起进入了同一家公司。王五是他们的上司，对张三非常赏识。赵六是王五的妻子，也认识李四..."
              resize="none"
            />
            <div class="text-config">
              <div class="config-row">
                <span class="config-label">窗口大小</span>
                <el-input-number v-model="textConfig.windowSize" :min="1" :max="20" size="small" />
              </div>
              <div class="config-row">
                <span class="config-label">最小共现</span>
                <el-input-number v-model="textConfig.minCoOccurrence" :min="1" :max="10" size="small" />
              </div>
            </div>
            <el-button
              type="primary"
              size="small"
              :loading="extracting"
              :disabled="!inputText.trim()"
              style="width: 100%; margin-top: 12px;"
              @click="handleExtractRelations"
            >
              <el-icon><MagicStick /></el-icon> 提取人物关系
            </el-button>

            <div v-if="extractResult" class="extract-result">
              <el-alert
                :title="extractResult.message"
                :type="extractResult.nodes?.length > 0 ? 'success' : 'warning'"
                :closable="false"
                show-icon
              />
            </div>

            <el-divider />

            <!-- 示例文本 -->
            <div class="section-header">
              <el-icon><Reading /></el-icon>
              <span>示例文本</span>
            </div>
            <div class="sample-texts">
              <el-button
                v-for="(sample, idx) in sampleTexts"
                :key="idx"
                size="small"
                plain
                style="width: 100%; margin-bottom: 6px; text-align: left;"
                @click="inputText = sample.text"
              >
                {{ sample.name }}
              </el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- 我的项目 Tab -->
        <el-tab-pane label="我的项目" name="projects">
          <div class="tab-section">
            <div class="section-header">
              <el-icon><FolderOpened /></el-icon>
              <span>已保存的项目</span>
              <el-button size="small" text type="primary" @click="loadProjects">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
            <div v-if="projects.length === 0" class="empty-projects">
              <el-empty description="暂无保存的项目" :image-size="60" />
            </div>
            <div v-else class="project-list">
              <div
                v-for="proj in projects"
                :key="proj.id"
                class="project-card"
              >
                <div class="project-info">
                  <div class="project-name">{{ proj.name }}</div>
                  <div class="project-meta">
                    <span>{{ proj.graph_data?.nodes?.length || 0 }}节点</span>
                    <span>{{ proj.created_at?.substring(0, 10) }}</span>
                  </div>
                </div>
                <div class="project-actions">
                  <el-button size="small" type="primary" text @click="loadProject(proj)">
                    <el-icon><View /></el-icon>
                  </el-button>
                  <el-button size="small" type="danger" text @click="handleDeleteProject(proj.id)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 统计信息 Tab -->
        <el-tab-pane label="统计信息" name="stats">
          <div class="tab-section">
            <div class="section-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>图数据统计</span>
              <el-button size="small" text type="primary" :disabled="!graphStore.nodeCount" @click="loadStats">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>

            <div v-if="!graphStore.nodeCount" class="empty-projects">
              <el-empty description="暂无数据，请先加载图数据" :image-size="60" />
            </div>

            <div v-else-if="graphStore.statsData" class="stats-content">
              <div class="stats-grid">
                <div class="stats-card">
                  <div class="stats-value">{{ graphStore.statsData.node_count }}</div>
                  <div class="stats-label">节点数</div>
                </div>
                <div class="stats-card">
                  <div class="stats-value">{{ graphStore.statsData.link_count }}</div>
                  <div class="stats-label">边数</div>
                </div>
                <div class="stats-card">
                  <div class="stats-value">{{ graphStore.statsData.density }}</div>
                  <div class="stats-label">图密度</div>
                </div>
                <div class="stats-card">
                  <div class="stats-value">{{ graphStore.statsData.avg_degree }}</div>
                  <div class="stats-label">平均度数</div>
                </div>
              </div>

              <div v-if="graphStore.statsData.max_degree_node" class="stats-detail">
                <div class="detail-title">度数最高节点</div>
                <div class="detail-value">
                  {{ graphStore.statsData.max_degree_node.name }}
                  (度数: {{ graphStore.statsData.max_degree_node.degree }})
                </div>
              </div>

              <div v-if="graphStore.statsData.relation_types" class="stats-detail">
                <div class="detail-title">关系类型分布</div>
                <div class="relation-tags">
                  <el-tag
                    v-for="(count, rel) in graphStore.statsData.relation_types"
                    :key="rel"
                    size="small"
                    type="info"
                    class="rel-tag"
                  >
                    {{ rel }}: {{ count }}
                  </el-tag>
                </div>
              </div>

              <div v-if="graphStore.statsData.category_stats" class="stats-detail">
                <div class="detail-title">分类统计</div>
                <div class="relation-tags">
                  <el-tag
                    v-for="(count, cat) in graphStore.statsData.category_stats"
                    :key="cat"
                    size="small"
                    class="rel-tag"
                  >
                    {{ cat }}: {{ count }}
                  </el-tag>
                </div>
              </div>

              <!-- 度数分布柱状图 -->
              <div class="detail-title" style="margin-top: 12px;">度数分布</div>
              <div ref="degreeChartRef" class="mini-chart"></div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 数据导出 Tab -->
        <el-tab-pane label="导出" name="export">
          <div class="tab-section">
            <div class="section-header">
              <el-icon><Download /></el-icon>
              <span>数据导出</span>
            </div>

            <div class="export-options">
              <el-button
                type="primary"
                plain
                size="small"
                :disabled="!graphStore.nodeCount"
                style="width: 100%; margin-bottom: 8px;"
                @click="handleExportJSON"
              >
                <el-icon><Download /></el-icon> 导出 JSON 数据
              </el-button>
            </div>

            <el-divider />

            <!-- 当前数据预览 -->
            <div class="section-header">
              <el-icon><View /></el-icon>
              <span>数据预览</span>
            </div>
            <div v-if="graphStore.nodeCount" class="data-preview">
              <el-collapse>
                <el-collapse-item title="节点列表" :name="1">
                  <div class="node-list">
                    <div
                      v-for="node in graphStore.graphData.nodes.slice(0, 50)"
                      :key="node.id"
                      class="preview-item"
                    >
                      <span class="preview-name">{{ node.name }}</span>
                      <span class="preview-value">{{ node.value }}</span>
                    </div>
                    <div v-if="graphStore.graphData.nodes.length > 50" class="preview-more">
                      ... 还有 {{ graphStore.graphData.nodes.length - 50 }} 个节点
                    </div>
                  </div>
                </el-collapse-item>
                <el-collapse-item title="关系列表" :name="2">
                  <div class="node-list">
                    <div
                      v-for="(link, idx) in graphStore.graphData.links.slice(0, 50)"
                      :key="idx"
                      class="preview-item"
                    >
                      <span class="preview-name">{{ getNodeName(link.source) }} → {{ getNodeName(link.target) }}</span>
                      <span class="preview-value">{{ link.relation || '-' }}</span>
                    </div>
                    <div v-if="graphStore.graphData.links.length > 50" class="preview-more">
                      ... 还有 {{ graphStore.graphData.links.length - 50 }} 条边
                    </div>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
            <div v-else class="empty-projects">
              <el-empty description="暂无数据" :image-size="60" />
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </aside>
</template>

<script setup>
import { ref, reactive, watch, nextTick, onMounted, onBeforeUnmount, markRaw } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useGraphStore } from '../../stores/chain-connect/graph'
import { datasetApi, projectApi, textApi, analysisApi, importExportApi } from '../../api/chain-connect'

const graphStore = useGraphStore()
const isCollapsed = ref(false)
const activeTab = ref('datasource')

// 数据集相关
const datasets = ref([])
const currentDatasetId = ref(null)

// 项目相关
const projects = ref([])
const saveProjectName = ref('')

// 文本提取相关
const inputText = ref('')
const extracting = ref(false)
const extractResult = ref(null)
const textConfig = reactive({
  windowSize: 3,
  minCoOccurrence: 1
})

// 统计图表
const degreeChartRef = ref(null)
let degreeChart = null

// 示例文本
const sampleTexts = [
  {
    name: '三国演义片段',
    text: `刘备与关羽、张飞桃园三结义，誓同生死。后来刘备三顾茅庐，请诸葛亮出山相助。诸葛亮字孔明，是当世大才。曹操统一北方后，率大军南下，刘备被迫逃往江夏。诸葛亮前往东吴，说服孙权与刘备联合抗曹。周瑜是东吴大都督，与诸葛亮合力在赤壁大败曹操。赤壁之战后，刘备借南郡，又取荆州四郡。关羽镇守荆州，张飞镇守阆中。赵云跟随刘备征战多年，忠心耿耿。刘备入川后，封诸葛亮为丞相，关羽为前将军，张飞为右将军，赵云为翊军将军。马超投降刘备后，被封为左将军。黄忠在定军山斩杀夏侯渊，立下大功。刘备称帝后，关羽大意失荆州，被孙权所杀。张飞闻讯后怒不可遏。刘备为报弟仇，率军伐吴，却在夷陵被陆逊火烧连营。刘备退回白帝城，托孤于诸葛亮。诸葛亮辅佐刘禅，六出祁山北伐曹魏，最终病逝于五丈原。司马懿是诸葛亮的主要对手，多次与诸葛亮交锋。姜维继承诸葛亮遗志，多次北伐，但终究未能成功。`
  },
  {
    name: '西游记片段',
    text: `唐僧受唐太宗之命前往西天取经。孙悟空是唐僧的大徒弟，本领高强，曾大闹天宫。猪八戒是唐僧的二徒弟，贪吃好色，原是天蓬元帅。沙悟净是唐僧的三徒弟，忠厚老实，原是卷帘大将。白龙马原是西海龙王三太子，因犯天条被贬，化为白马载唐僧西行。观音菩萨指引唐僧收服三个徒弟。取经途中，孙悟空多次与妖魔鬼怪战斗。牛魔王是孙悟空的结拜兄弟，后因铁扇公主之事反目。红孩儿是牛魔王和铁扇公主之子，被观音收服。白骨精三次变化，欺骗唐僧，孙悟空火眼金睛识破，却被唐僧误解。金角大王和银角大王是太上老君的童子，下界为妖。黄袍怪原是天上奎木狼星君下凡。蜘蛛精在盘丝洞设计捉拿唐僧。玉兔精假扮天竺公主。如来佛祖在灵山等待唐僧师徒到来，最终赐予真经。`
  },
  {
    name: '公司关系示例',
    text: `张伟是公司的CEO，负责整体战略规划。李芳是CTO，直接向张伟汇报工作。陈明是研发部经理，是李芳的下属。王丽是产品经理，与陈明经常合作讨论产品需求。赵强是市场部总监，和张伟是大学同学。刘洋是财务总监，与赵强经常沟通营销预算。孙悦是设计师，在王丽的项目组中负责界面设计。周磊是后端工程师，是陈明的团队成员。吴婷是前端工程师，和周磊搭档开发。郑凯是测试工程师，负责吴婷和周磊开发的产品测试。黄鑫是实习生，陈明是他的导师。张伟非常信任李芳的技术判断。赵强和李芳有时会因为资源分配产生分歧。王丽认为孙悦的设计能力很强。刘洋对周磊的加班申请表示了关注。`
  }
]

function handleModuleChangeEvent(e) {
  const mod = e.detail.module
  if (mod === 'social') activeTab.value = 'datasource'
  else if (mod === 'text') activeTab.value = 'text'
  else if (mod === 'projects') activeTab.value = 'projects'
}

onMounted(() => {
  loadDatasets()
  loadProjects()
  window.addEventListener('module-change', handleModuleChangeEvent)
})

onBeforeUnmount(() => {
  window.removeEventListener('module-change', handleModuleChangeEvent)
  if (degreeChart) {
    degreeChart.dispose()
    degreeChart = null
  }
})

// ========== 数据集操作 ==========
async function loadDatasets() {
  try {
    const res = await datasetApi.getAll()
    if (res.code === 200) {
      datasets.value = res.data
    }
  } catch (e) {
    console.error('加载数据集失败', e)
  }
}

function loadDataset(ds) {
  currentDatasetId.value = ds.id
  graphStore.setGraphData(ds.graph_data)
  graphStore.setDataSource({ type: 'dataset', name: ds.name, description: ds.description })
  ElMessage.success(`已加载数据集: ${ds.name}`)
  // 自动获取统计信息
  loadStats()
}

// ========== 文件上传 ==========
function handleFileUpload(file) {
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const jsonData = JSON.parse(e.target.result)
      const res = await importExportApi.importJson(jsonData)
      if (res.code === 200) {
        graphStore.setGraphData(res.data)
        graphStore.setDataSource({ type: 'import', name: file.name, description: '从文件导入' })
        currentDatasetId.value = null
        ElMessage.success(res.message)
        loadStats()
      }
    } catch (err) {
      ElMessage.error('JSON 文件解析失败，请检查格式')
    }
  }
  reader.readAsText(file.raw)
}

// ========== 文本提取 ==========
async function handleExtractRelations() {
  extracting.value = true
  extractResult.value = null
  try {
    const res = await textApi.extract({
      text: inputText.value,
      window_size: textConfig.windowSize,
      min_co_occurrence: textConfig.minCoOccurrence
    })
    if (res.code === 200) {
      extractResult.value = { message: res.message, nodes: res.data.nodes }
      if (res.data.nodes.length > 0) {
        graphStore.setGraphData(res.data)
        graphStore.setDataSource({ type: 'text', name: '文本提取结果', description: '从输入文本中提取的人物关系' })
        currentDatasetId.value = null
        loadStats()
      }
    }
  } catch (e) {
    ElMessage.error('文本处理失败')
  } finally {
    extracting.value = false
  }
}

// ========== 项目操作 ==========
async function loadProjects() {
  try {
    const res = await projectApi.getAll()
    if (res.code === 200) {
      projects.value = res.data
    }
  } catch (e) {
    console.error('加载项目失败', e)
  }
}

async function handleSaveProject() {
  if (!saveProjectName.value.trim()) return
  try {
    const res = await projectApi.create({
      name: saveProjectName.value,
      description: graphStore.dataSource.description || '',
      data_type: graphStore.dataSource.type || 'social',
      graph_data: graphStore.graphData,
      layout_config: graphStore.layoutConfig,
      visual_config: graphStore.visualConfig
    })
    if (res.code === 200) {
      ElMessage.success('项目保存成功')
      saveProjectName.value = ''
      loadProjects()
    }
  } catch (e) {
    // 错误在拦截器处理
  }
}

function loadProject(proj) {
  graphStore.setGraphData(proj.graph_data)
  graphStore.setDataSource({ type: 'project', name: proj.name, description: proj.description })
  if (proj.layout_config && Object.keys(proj.layout_config).length > 0) {
    Object.keys(proj.layout_config).forEach(key => {
      graphStore.updateLayoutConfig(key, proj.layout_config[key])
    })
  }
  if (proj.visual_config && Object.keys(proj.visual_config).length > 0) {
    graphStore.updateVisualConfig(proj.visual_config)
  }
  currentDatasetId.value = null
  ElMessage.success(`已加载项目: ${proj.name}`)
  loadStats()
}

async function handleDeleteProject(id) {
  try {
    await ElMessageBox.confirm('确定要删除该项目吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    const res = await projectApi.delete(id)
    if (res.code === 200) {
      ElMessage.success('项目已删除')
      loadProjects()
    }
  } catch (e) {
    // 用户取消
  }
}

// ========== 统计分析 ==========
async function loadStats() {
  if (!graphStore.nodeCount) return
  try {
    const res = await analysisApi.getStats(graphStore.graphData)
    if (res.code === 200) {
      graphStore.setStatsData(res.data)
      nextTick(() => renderDegreeChart())
    }
  } catch (e) {
    console.error('加载统计失败', e)
  }
}

function renderDegreeChart() {
  if (!degreeChartRef.value || !graphStore.statsData?.degree_distribution) return

  if (degreeChart) {
    degreeChart.dispose()
  }
  degreeChart = markRaw(echarts.init(degreeChartRef.value))

  const degreeDist = graphStore.statsData.degree_distribution
  // 统计度数分布
  const degreeCount = {}
  Object.values(degreeDist).forEach(d => {
    degreeCount[d] = (degreeCount[d] || 0) + 1
  })

  const xData = Object.keys(degreeCount).sort((a, b) => Number(a) - Number(b))
  const yData = xData.map(k => degreeCount[k])

  degreeChart.setOption({
    grid: { left: 40, right: 10, top: 10, bottom: 30 },
    xAxis: {
      type: 'category',
      data: xData,
      name: '度数',
      nameTextStyle: { fontSize: 10 },
      axisLabel: { fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      name: '数量',
      nameTextStyle: { fontSize: 10 },
      axisLabel: { fontSize: 10 }
    },
    series: [{
      type: 'bar',
      data: yData,
      itemStyle: {
        color: '#409EFF',
        borderRadius: [4, 4, 0, 0]
      }
    }]
  })
}

// ========== 导出 ==========
function handleExportJSON() {
  const data = JSON.stringify(graphStore.graphData, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.download = `graph-data-${Date.now()}.json`
  link.href = url
  link.click()
  URL.revokeObjectURL(url)
  ElMessage.success('JSON 数据已导出')
}

function getNodeName(id) {
  const node = graphStore.graphData.nodes.find(n => n.id === id)
  return node ? node.name : id
}

// 监听 tab 切换到统计时自动加载
watch(activeTab, (val) => {
  if (val === 'stats' && graphStore.nodeCount) {
    if (!graphStore.statsData) {
      loadStats()
    } else {
      nextTick(() => renderDegreeChart())
    }
  }
  if (val === 'projects') {
    loadProjects()
  }
})
</script>

<style scoped>
.right-panel {
  width: 340px;
  background: #fff;
  border-left: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  position: relative;
  flex-shrink: 0;
  transition: width 0.3s ease;
  overflow: hidden;
}

.right-panel.collapsed {
  width: 40px;
}

.panel-toggle {
  position: absolute;
  top: 8px;
  left: 8px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 4px;
  z-index: 10;
  color: #909399;
  transition: all 0.2s;
}

.panel-toggle:hover {
  background: #f5f7fa;
  color: #409EFF;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

:deep(.panel-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.panel-tabs .el-tabs__header) {
  margin: 0;
  padding: 0 8px;
}

:deep(.panel-tabs .el-tabs__content) {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

:deep(.panel-tabs .el-tab-pane) {
  padding: 0 12px 12px;
}

:deep(.panel-tabs .el-tabs__item) {
  font-size: 12px;
  padding: 0 10px;
  height: 38px;
}

.tab-section {
  padding-top: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

/* 数据集卡片 */
.dataset-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dataset-card {
  padding: 10px 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.dataset-card:hover {
  border-color: #409EFF;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.15);
}

.dataset-card.active {
  border-color: #409EFF;
  background: #ecf5ff;
}

.dataset-name {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.dataset-desc {
  font-size: 11px;
  color: #909399;
  margin-bottom: 6px;
  line-height: 1.4;
}

.dataset-meta {
  display: flex;
  gap: 6px;
}

/* 保存表单 */
.save-form {
  display: flex;
  gap: 8px;
}

/* 文本配置 */
.text-config {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-row .config-label {
  font-size: 12px;
  color: #606266;
  min-width: 64px;
}

.extract-result {
  margin-top: 12px;
}

.sample-texts {
  display: flex;
  flex-direction: column;
}

/* 项目列表 */
.project-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.project-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  transition: all 0.2s;
}

.project-card:hover {
  border-color: #c6e2ff;
  background: #f5f7fa;
}

.project-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.project-meta {
  font-size: 11px;
  color: #909399;
  display: flex;
  gap: 8px;
  margin-top: 2px;
}

.project-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

/* 统计 */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.stats-card {
  text-align: center;
  padding: 12px 8px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stats-value {
  font-size: 22px;
  font-weight: 700;
  color: #409EFF;
}

.stats-label {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.stats-detail {
  margin-bottom: 10px;
}

.detail-title {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 6px;
}

.detail-value {
  font-size: 13px;
  color: #303133;
}

.relation-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.rel-tag {
  font-size: 11px;
}

.mini-chart {
  width: 100%;
  height: 160px;
}

/* 导出与预览 */
.data-preview {
  max-height: 400px;
  overflow-y: auto;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 12px;
  border-bottom: 1px solid #f5f7fa;
}

.preview-name {
  color: #303133;
}

.preview-value {
  color: #909399;
}

.preview-more {
  font-size: 12px;
  color: #909399;
  padding: 4px 0;
  text-align: center;
}

.empty-projects {
  padding: 20px 0;
}

:deep(.el-divider) {
  margin: 12px 0;
}

.json-upload {
  width: 100%;
}
</style>
