<template>
  <div>
    <el-tabs v-model="activeTab" type="border-card">
      <!-- ==================== Tab 1: PCA 降维权重 ==================== -->
      <el-tab-pane label="PCA 多维属性降权" name="pca">
        <div class="analysis-section">
          <el-alert type="info" :closable="false" show-icon style="margin-bottom:20px">
            <template #title>
              从已有数据集的树节点中提取所有数值属性（如收入、人数、面积等），
              使用 PCA 降到 1 维，得到综合权重作为 Voronoi 面积编码。
            </template>
          </el-alert>

          <el-form label-width="120px" style="max-width:500px">
            <el-form-item label="选择数据集">
              <el-select v-model="pcaDatasetId" placeholder="选择一个数据集" filterable style="width:100%"
                         :loading="listLoading">
                <el-option v-for="ds in allDatasets" :key="ds.id" :label="ds.name" :value="ds.id">
                  <span>{{ ds.name }}</span>
                  <span style="float:right;color:#909399;font-size:12px">{{ ds.node_count }} 节点</span>
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="pcaLoading" :disabled="!pcaDatasetId" @click="runPca">
                执行 PCA 降维
              </el-button>
            </el-form-item>
          </el-form>

          <!-- PCA 结果 -->
          <template v-if="pcaResult">
            <el-divider content-position="left">分析结果</el-divider>

            <div class="analysis-result-grid">
              <el-card shadow="never">
                <template #header><span style="font-weight:600">PCA 分析信息</span></template>
                <el-descriptions :column="1" border size="small">
                  <el-descriptions-item label="使用特征数">{{ pcaResult.analysis.features_used.length }}</el-descriptions-item>
                  <el-descriptions-item label="特征列表">{{ pcaResult.analysis.features_used.join(', ') }}</el-descriptions-item>
                  <el-descriptions-item label="方差解释率">{{ (pcaResult.analysis.explained_variance_ratio * 100).toFixed(1) }}%</el-descriptions-item>
                  <el-descriptions-item label="节点数量">{{ pcaResult.analysis.n_nodes }}</el-descriptions-item>
                  <el-descriptions-item label="权重范围">{{ pcaResult.analysis.weight_stats.min }} ~ {{ pcaResult.analysis.weight_stats.max }}</el-descriptions-item>
                </el-descriptions>
              </el-card>

              <el-card shadow="never">
                <template #header><span style="font-weight:600">特征贡献度 (主成分载荷)</span></template>
                <div class="feature-bars">
                  <div v-for="(val, key) in pcaResult.analysis.feature_importance" :key="key" class="feature-bar-row">
                    <span class="feature-name">{{ key }}</span>
                    <div class="feature-bar-track">
                      <div class="feature-bar-fill"
                           :style="{ width: Math.abs(val) / maxImportance * 100 + '%', background: val >= 0 ? '#409eff' : '#e6a23c' }">
                      </div>
                    </div>
                    <span class="feature-val">{{ val }}</span>
                  </div>
                </div>
              </el-card>
            </div>

            <div style="margin-top:20px;display:flex;gap:12px">
              <el-button type="success" @click="visualizePcaResult">
                打开 Voronoi 可视化
              </el-button>
            </div>
          </template>
        </div>
      </el-tab-pane>

      <!-- ==================== Tab 2: CSV 聚类建树 ==================== -->
      <el-tab-pane label="CSV 降维聚类建树" name="cluster">
        <div class="analysis-section">
          <el-alert type="info" :closable="false" show-icon style="margin-bottom:20px">
            <template #title>
              上传 CSV 表格数据，自动选取数值列进行标准化，通过 PCA 或 t-SNE 降至 2 维，
              再用层次聚类（Agglomerative Clustering）自动分组，生成树形结构供 Voronoi 可视化。
            </template>
          </el-alert>

          <el-form label-width="120px" style="max-width:560px">
            <el-form-item label="上传 CSV">
              <el-upload ref="csvUploadRef" :auto-upload="false" :limit="1" accept=".csv"
                         :on-change="handleCsvChange" :on-remove="handleCsvRemove" drag>
                <el-icon style="font-size:36px;color:#c0c4cc"><UploadFilled /></el-icon>
                <div style="margin-top:6px;color:#606266">拖拽 CSV 文件到此处或 <em>点击选择</em></div>
              </el-upload>
            </el-form-item>
            <el-form-item label="降维算法">
              <el-radio-group v-model="clusterMethod">
                <el-radio-button value="pca">PCA</el-radio-button>
                <el-radio-button value="tsne">t-SNE</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="标签列 (可选)">
              <el-input v-model="labelColumn" placeholder="指定行名列名，如 name / city / id" />
            </el-form-item>
            <el-form-item label="聚类数量">
              <el-input-number v-model="nClusters" :min="2" :max="20" placeholder="留空自动" />
              <span style="margin-left:8px;font-size:12px;color:#909399">留空自动决定</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="clusterLoading" :disabled="!csvFile" @click="runCluster">
                执行降维聚类
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 聚类结果 -->
          <template v-if="clusterResult">
            <el-divider content-position="left">分析结果</el-divider>

            <div class="analysis-result-grid">
              <el-card shadow="never">
                <template #header><span style="font-weight:600">数据与降维信息</span></template>
                <el-descriptions :column="1" border size="small">
                  <el-descriptions-item label="样本数">{{ clusterResult.analysis.data_info.n_samples }}</el-descriptions-item>
                  <el-descriptions-item label="特征数">{{ clusterResult.analysis.data_info.n_features }}</el-descriptions-item>
                  <el-descriptions-item label="特征列表">{{ clusterResult.analysis.data_info.feature_names.join(', ') }}</el-descriptions-item>
                  <el-descriptions-item label="降维算法">{{ clusterResult.analysis.reduction.method }}</el-descriptions-item>
                  <el-descriptions-item v-if="clusterResult.analysis.reduction.explained_variance_ratio" label="方差解释率">
                    {{ clusterResult.analysis.reduction.explained_variance_ratio.map(v => (v*100).toFixed(1)+'%').join(' + ') }}
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>

              <el-card shadow="never">
                <template #header><span style="font-weight:600">聚类信息</span></template>
                <el-descriptions :column="1" border size="small">
                  <el-descriptions-item label="聚类算法">{{ clusterResult.analysis.clustering.method }}</el-descriptions-item>
                  <el-descriptions-item label="聚类数">{{ clusterResult.analysis.clustering.n_clusters }}</el-descriptions-item>
                  <el-descriptions-item v-for="(count, name) in clusterResult.analysis.clustering.cluster_sizes"
                                        :key="name" :label="name">
                    {{ count }} 个样本
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>
            </div>

            <!-- 散点图 -->
            <el-card shadow="never" style="margin-top:20px">
              <template #header><span style="font-weight:600">降维散点图（按聚类着色）</span></template>
              <ScatterPlot :data="clusterResult.analysis.scatter_data" :height="380" />
            </el-card>

            <div style="margin-top:20px;display:flex;gap:12px;flex-wrap:wrap">
              <el-button type="success" @click="visualizeClusterResult">
                打开 Voronoi 可视化
              </el-button>
              <el-button type="primary" @click="saveDialogVisible = true">
                保存为数据集
              </el-button>
            </div>
          </template>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 保存对话框 -->
    <el-dialog v-model="saveDialogVisible" title="保存聚类结果为数据集" width="460px">
      <el-form label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="saveName" placeholder="数据集名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="saveDescription" type="textarea" :rows="3" placeholder="描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saveLoading" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDatasetStore } from '../../stores/voronoi/dataset'
import { getDatasets } from '../../api/voronoi/dataset'
import { applyPcaWeight, clusterCsv, saveClusterResult } from '../../api/voronoi/analysis'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import ScatterPlot from '../../components/voronoi/ScatterPlot.vue'

const router = useRouter()
const datasetStore = useDatasetStore()

const activeTab = ref('pca')
const allDatasets = ref([])
const listLoading = ref(false)

const pcaDatasetId = ref(null)
const pcaLoading = ref(false)
const pcaResult = ref(null)

const csvFile = ref(null)
const csvUploadRef = ref(null)
const clusterMethod = ref('pca')
const labelColumn = ref('')
const nClusters = ref(null)
const clusterLoading = ref(false)
const clusterResult = ref(null)

const saveDialogVisible = ref(false)
const saveName = ref('')
const saveDescription = ref('')
const saveLoading = ref(false)

const maxImportance = computed(() => {
  if (!pcaResult.value?.analysis?.feature_importance) return 1
  const vals = Object.values(pcaResult.value.analysis.feature_importance)
  return Math.max(...vals.map(Math.abs), 0.01)
})

onMounted(async () => {
  listLoading.value = true
  try {
    const res = await getDatasets({ per_page: 200 })
    allDatasets.value = res.data.items
  } catch { /* handled by interceptor */ }
  finally { listLoading.value = false }
})

async function runPca() {
  if (!pcaDatasetId.value) return
  pcaLoading.value = true
  pcaResult.value = null
  try {
    const res = await applyPcaWeight(pcaDatasetId.value)
    pcaResult.value = res.data
    ElMessage.success('PCA 降维分析完成')
  } catch (err) {
    ElMessage.error(err?.message || 'PCA 分析失败')
  } finally {
    pcaLoading.value = false
  }
}

function visualizePcaResult() {
  if (!pcaResult.value?.tree_data) return
  datasetStore.currentTreeData = pcaResult.value.tree_data
  datasetStore.currentDataset = pcaResult.value.dataset_info || null
  router.push('/voronoi/visualization')
}

function handleCsvChange(file) { csvFile.value = file.raw }
function handleCsvRemove() { csvFile.value = null }

async function runCluster() {
  if (!csvFile.value) return
  clusterLoading.value = true
  clusterResult.value = null
  try {
    const fd = new FormData()
    fd.append('file', csvFile.value)
    fd.append('method', clusterMethod.value)
    if (labelColumn.value.trim()) fd.append('label_column', labelColumn.value.trim())
    if (nClusters.value) fd.append('n_clusters', nClusters.value)

    const res = await clusterCsv(fd)
    clusterResult.value = res.data
    ElMessage.success('降维聚类分析完成')
  } catch (err) {
    ElMessage.error(err?.message || '聚类分析失败')
  } finally {
    clusterLoading.value = false
  }
}

function visualizeClusterResult() {
  if (!clusterResult.value?.tree_data) return
  datasetStore.currentTreeData = clusterResult.value.tree_data
  datasetStore.currentDataset = {
    name: '聚类分析结果',
    node_count: '-',
    max_depth: '-',
    leaf_count: '-',
  }
  router.push('/voronoi/visualization')
}

async function handleSave() {
  if (!clusterResult.value?.tree_data) return
  saveLoading.value = true
  try {
    await saveClusterResult({
      tree_data: clusterResult.value.tree_data,
      name: saveName.value || '聚类分析结果',
      description: saveDescription.value,
    })
    ElMessage.success('已保存为数据集')
    saveDialogVisible.value = false
    saveName.value = ''
    saveDescription.value = ''
  } catch (err) {
    ElMessage.error(err?.message || '保存失败')
  } finally {
    saveLoading.value = false
  }
}
</script>
