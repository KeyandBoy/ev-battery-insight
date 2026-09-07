<template>
  <div class="view-stack">
    <el-row :gutter="20">
      <el-col :xs="24" :xl="9">
        <el-card class="glass-card studio-card" shadow="never">
          <div class="section-split">
            <div>
              <h3>数据集目录</h3>
              <p>生成模拟样本、切换当前数据集，并快速查看当前工程中的数据规模。</p>
            </div>
            <el-button plain @click="workspace.refreshAll">刷新</el-button>
          </div>

          <div class="studio-action-grid">
            <el-button
              type="primary"
              :loading="workspace.loading.generate"
              @click="workspace.generateSampleDataset('gene_expression')"
            >
              基因表达
            </el-button>
            <el-button
              type="success"
              :loading="workspace.loading.generate"
              @click="workspace.generateSampleDataset('image_features')"
            >
              图像特征
            </el-button>
            <el-button
              type="warning"
              :loading="workspace.loading.generate"
              @click="workspace.generateSampleDataset('finance_behavior')"
            >
              金融行为
            </el-button>
          </div>

          <div class="studio-quick-stats">
            <div class="mini-card">
              <strong>当前数据集</strong>
              <span>{{ workspace.currentDataset.value?.name || "未选择" }}</span>
            </div>
            <div class="mini-card">
              <strong>样本数</strong>
              <span>{{ workspace.currentDataset.value?.sampleCount ?? 0 }}</span>
            </div>
            <div class="mini-card">
              <strong>维度数</strong>
              <span>{{ workspace.currentDataset.value?.dimensionCount ?? 0 }}</span>
            </div>
          </div>

          <el-table
            class="studio-directory-table"
            :data="workspace.datasets.value"
            height="360"
            highlight-current-row
            @current-change="handleDatasetSelect"
            :row-class-name="rowClassName"
          >
            <el-table-column prop="name" label="名称" min-width="220" />
            <el-table-column prop="sampleCount" label="样本" width="92" />
            <el-table-column prop="dimensionCount" label="维度" width="92" />
            <el-table-column label="" width="72" fixed="right">
              <template #default="{ row }">
                <el-popconfirm
                  title="将同时删除该数据集的所有历史运行，确认删除？"
                  confirm-button-text="删除"
                  cancel-button-text="取消"
                  confirm-button-type="danger"
                  width="220"
                  @confirm="workspace.removeDataset(row.id)"
                >
                  <template #reference>
                    <el-button size="small" type="danger" plain @click.stop>删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :xl="15">
        <el-card class="glass-card studio-card" shadow="never">
          <div class="section-split">
            <div>
              <h3>数据接入</h3>
              <p>上传 CSV、补充标签列，并在导入前明确数据来源和分析背景。</p>
            </div>
            <el-tag type="info" effect="plain">CSV / Label Ready</el-tag>
          </div>

          <div class="studio-ingest">
            <el-form label-position="top" class="form-panel studio-form">
              <el-form-item label="数据集名称">
                <el-input v-model="uploadForm.name" placeholder="例如：customer_risk_profile" />
              </el-form-item>
              <el-form-item label="标签列">
                <el-input v-model="uploadForm.labelColumn" placeholder="默认 label" />
              </el-form-item>
              <el-form-item label="数据集描述" class="studio-form__wide">
                <el-input
                  v-model="uploadForm.description"
                  type="textarea"
                  :rows="4"
                  placeholder="描述数据来源、业务背景和使用目标"
                />
              </el-form-item>
            </el-form>

            <div class="studio-upload-panel">
              <div class="studio-upload-panel__head">
                <strong>CSV 文件</strong>
                <span>建议包含标签列，便于区域结果解释与质量评估。</span>
              </div>
              <el-upload
                class="studio-upload"
                drag
                :auto-upload="false"
                :show-file-list="true"
                :limit="1"
                accept=".csv"
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">将 CSV 拖到此处，或 <em>点击上传</em></div>
              </el-upload>
              <el-button type="primary" :loading="workspace.loading.upload" @click="submitUpload">上传数据集</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="glass-card studio-card" shadow="never">
      <div class="section-split">
        <div>
          <h3>分析配置</h3>
          <p>按预处理、降维、聚类三阶段组织参数，支持一键运行完整分析与快速重置。</p>
        </div>
        <el-space>
          <el-button plain @click="workspace.resetConfig">重置</el-button>
          <el-button type="primary" :loading="workspace.loading.analysis" @click="workspace.submitAnalysis">
            运行完整分析
          </el-button>
        </el-space>
      </div>

      <el-tabs type="border-card" class="studio-tabs">
        <el-tab-pane label="预处理">
          <el-form label-position="top" class="studio-grid">
            <el-form-item label="标签列">
              <el-input v-model="workspace.config.preprocess.labelColumn" />
            </el-form-item>
            <el-form-item label="缺失值填充">
              <el-select v-model="workspace.config.preprocess.missingStrategy">
                <el-option label="median" value="median" />
                <el-option label="mean" value="mean" />
                <el-option label="most_frequent" value="most_frequent" />
              </el-select>
            </el-form-item>
            <el-form-item label="标准化方式">
              <el-select v-model="workspace.config.preprocess.scaler">
                <el-option label="standard" value="standard" />
                <el-option label="minmax" value="minmax" />
                <el-option label="robust" value="robust" />
                <el-option label="none" value="none" />
              </el-select>
            </el-form-item>
            <el-form-item label="方差阈值">
              <el-input-number v-model="workspace.config.preprocess.varianceThreshold" :step="0.01" :min="0" />
            </el-form-item>
            <el-form-item label="相关性阈值">
              <el-input-number
                v-model="workspace.config.preprocess.correlationThreshold"
                :step="0.01"
                :min="0"
                :max="0.9999"
              />
            </el-form-item>
            <el-form-item label="最大保留维度">
              <el-input-number v-model="workspace.config.preprocess.maxFeatures" :min="2" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="降维">
          <el-form label-position="top" class="studio-grid">
            <el-form-item label="降维方法">
              <el-select v-model="workspace.config.reduction.method">
                <el-option label="UMAP" value="umap" />
                <el-option label="PCA" value="pca" />
                <el-option label="t-SNE" value="tsne" />
              </el-select>
            </el-form-item>
            <el-form-item label="输出维度">
              <el-input-number v-model="workspace.config.reduction.nComponents" :min="1" :max="3" />
            </el-form-item>
            <el-form-item label="UMAP 邻居数">
              <el-input-number v-model="workspace.config.reduction.neighbors" :min="2" />
            </el-form-item>
            <el-form-item label="UMAP 最小距离">
              <el-input-number v-model="workspace.config.reduction.minDist" :step="0.01" :min="0" :max="1" />
            </el-form-item>
            <el-form-item label="t-SNE perplexity">
              <el-input-number v-model="workspace.config.reduction.perplexity" :min="1" />
            </el-form-item>
            <el-form-item label="t-SNE learning rate">
              <el-input-number v-model="workspace.config.reduction.learningRate" :min="10" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="聚类">
          <el-form label-position="top" class="studio-grid">
            <el-form-item label="聚类方法">
              <el-select v-model="workspace.config.clustering.method">
                <el-option label="DBSCAN" value="dbscan" />
                <el-option label="KMeans" value="kmeans" />
                <el-option label="Agglomerative" value="agglomerative" />
              </el-select>
            </el-form-item>
            <el-form-item label="DBSCAN eps">
              <el-input-number v-model="workspace.config.clustering.eps" :step="0.05" :min="0.01" />
            </el-form-item>
            <el-form-item label="DBSCAN min_samples">
              <el-input-number v-model="workspace.config.clustering.minSamples" :min="2" />
            </el-form-item>
            <el-form-item label="聚类数">
              <el-input-number v-model="workspace.config.clustering.clusters" :min="2" />
            </el-form-item>
            <el-form-item label="层次聚类 linkage">
              <el-select v-model="workspace.config.clustering.linkage">
                <el-option label="ward" value="ward" />
                <el-option label="complete" value="complete" />
                <el-option label="average" value="average" />
              </el-select>
            </el-form-item>
            <el-form-item label="密度带宽">
              <el-input-number v-model="workspace.config.clustering.densityBandwidth" :step="0.05" :min="0.01" />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-card class="glass-card" shadow="never">
      <DatasetSummaryPanel :summary="workspace.datasetSummary.value" />
    </el-card>

    <el-row :gutter="20">
      <el-col :xs="24" :xl="12">
        <el-card class="glass-card" shadow="never">
          <LabelMosaicChart :distribution="workspace.datasetSummary.value?.labelDistribution || {}" />
        </el-card>
      </el-col>
      <el-col :xs="24" :xl="12">
        <el-card class="glass-card" shadow="never">
          <VarianceBarChart :features="workspace.datasetSummary.value?.featureOverview?.topVarianceFeatures || []" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, reactive } from "vue";
import { UploadFilled } from "@element-plus/icons-vue";
import DatasetSummaryPanel from "../../components/region/DatasetSummaryPanel.vue";
import LabelMosaicChart from "../../components/region/LabelMosaicChart.vue";
import VarianceBarChart from "../../components/region/VarianceBarChart.vue";
import { useWorkspace } from "../../composables/region/useWorkspace";

const workspace = useWorkspace();

onMounted(async () => {
  if (workspace.selectedDatasetId.value) {
    await workspace.chooseDataset(workspace.selectedDatasetId.value, { preserveAnalysis: true });
  }
});

const uploadForm = reactive({
  name: "",
  description: "",
  labelColumn: "label",
  file: null
});

function handleFileChange(file) {
  uploadForm.file = file.raw;
}

function handleFileRemove() {
  uploadForm.file = null;
}

async function submitUpload() {
  await workspace.uploadCsvDataset(uploadForm);
  uploadForm.name = "";
  uploadForm.description = "";
  uploadForm.labelColumn = "label";
  uploadForm.file = null;
}

function handleDatasetSelect(row) {
  if (row?.id) {
    workspace.chooseDataset(row.id);
  }
}

function rowClassName({ row }) {
  return row.id === workspace.selectedDatasetId.value ? "is-selected-row" : "";
}
</script>
