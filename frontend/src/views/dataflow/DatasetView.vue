<script setup>
import { onMounted, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { CollectionTag, DataAnalysis, UploadFilled } from "@element-plus/icons-vue";

import {
  deleteDatasetById,
  fetchDatasetPreview,
  fetchDatasets,
  uploadDataset,
} from "../../api/dataflow/dataset";

const uploadRef = ref(null);
const loading = ref(false);
const uploading = ref(false);
const previewLoading = ref(false);
const datasets = ref([]);
const summary = ref(null);
const latestUploadedDatasetId = ref(null);
const latestUploadedDatasetName = ref("");

const form = reactive({
  name: "",
  hierarchy_fields: "",
  value_field: "",
});

const fileState = reactive({
  file: null,
  fileName: "",
});

const previewDialog = reactive({
  visible: false,
  activeTab: "processed",
  title: "",
  columns: [],
  rows: [],
  totalRows: 0,
  previewCount: 0,
  processedColumns: [],
  processedRows: [],
  processedTotalRows: 0,
  processedPreviewCount: 0,
});

function handleFileChange(uploadFile) {
  fileState.file = uploadFile?.raw || null;
  fileState.fileName = uploadFile?.name || "";
}

function handleFileExceed() {
  ElMessage.warning("一次仅支持选择 1 个文件");
}

function clearFile() {
  fileState.file = null;
  fileState.fileName = "";
  if (uploadRef.value) {
    uploadRef.value.clearFiles();
  }
}

async function loadDatasets() {
  loading.value = true;
  try {
    const result = await fetchDatasets(1, 100);
    datasets.value = result?.data || [];
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loading.value = false;
  }
}

async function handleUpload() {
  if (!fileState.file) {
    ElMessage.warning("请先选择上传文件");
    return;
  }

  uploading.value = true;
  try {
    const formData = new FormData();
    formData.append("file", fileState.file);
    if (form.name) {
      formData.append("name", form.name);
    }
    if (form.hierarchy_fields) {
      formData.append("hierarchy_fields", form.hierarchy_fields);
    }
    if (form.value_field) {
      formData.append("value_field", form.value_field);
    }

    const result = await uploadDataset(formData);
    summary.value = result?.data?.summary || null;
    latestUploadedDatasetId.value = result?.data?.dataset?.id || null;
    latestUploadedDatasetName.value = result?.data?.dataset?.name || "";
    ElMessage.success(result?.message || "上传成功");
    clearFile();
    await loadDatasets();
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    uploading.value = false;
  }
}

function resetPreviewDialog() {
  previewDialog.activeTab = "processed";
  previewDialog.title = "";
  previewDialog.columns = [];
  previewDialog.rows = [];
  previewDialog.totalRows = 0;
  previewDialog.previewCount = 0;
  previewDialog.processedColumns = [];
  previewDialog.processedRows = [];
  previewDialog.processedTotalRows = 0;
  previewDialog.processedPreviewCount = 0;
}

async function openPreview(datasetId, datasetName) {
  previewLoading.value = true;
  previewDialog.visible = true;
  previewDialog.title = `数据集预览 - ${datasetName}`;
  try {
    const result = await fetchDatasetPreview(datasetId, 20);
    const preview = result?.data?.preview || {};
    const processedPreview = result?.data?.processed_preview || {};
    previewDialog.columns = preview.columns || [];
    previewDialog.rows = preview.rows || [];
    previewDialog.totalRows = preview.total_rows || 0;
    previewDialog.previewCount = preview.preview_count || 0;
    previewDialog.processedColumns = processedPreview.columns || [];
    previewDialog.processedRows = processedPreview.rows || [];
    previewDialog.processedTotalRows = processedPreview.total_rows || 0;
    previewDialog.processedPreviewCount = processedPreview.preview_count || 0;
    previewDialog.activeTab = previewDialog.processedRows.length ? "processed" : "raw";
  } catch (error) {
    previewDialog.visible = false;
    ElMessage.error(error.message);
  } finally {
    previewLoading.value = false;
  }
}

async function handlePreview(row) {
  await openPreview(row.id, row.name || `ID ${row.id}`);
}

async function handlePreviewLatest() {
  if (!latestUploadedDatasetId.value) {
    ElMessage.warning("当前没有可预览的上传结果");
    return;
  }
  await openPreview(latestUploadedDatasetId.value, latestUploadedDatasetName.value || "最新上传数据集");
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确认删除数据集「${row.name}」吗？此操作会删除关联记录，且无法恢复。`,
      "删除确认",
      {
        confirmButtonText: "确认删除",
        cancelButtonText: "取消",
        type: "warning",
      }
    );
  } catch {
    return;
  }

  try {
    await deleteDatasetById(row.id);
    ElMessage.success("数据集已删除");
    if (latestUploadedDatasetId.value === row.id) {
      latestUploadedDatasetId.value = null;
      latestUploadedDatasetName.value = "";
    }
    if (previewDialog.visible && previewDialog.title.includes(String(row.name))) {
      previewDialog.visible = false;
      resetPreviewDialog();
    }
    await loadDatasets();
  } catch (error) {
    ElMessage.error(error.message);
  }
}

function handlePreviewDialogClosed() {
  resetPreviewDialog();
}

onMounted(async () => {
  await loadDatasets();
});
</script>

<template>
  <div class="page-wrap feature-page">
    <el-card shadow="never" class="feature-hero-card">
      <div class="feature-hero-head">
        <div>
          <h2>数据集管理</h2>
          <p>
            导入层次数据文件，完成清洗、结构识别与入库。支持上传后预览，以及在数据集列表中快速预览和删除。
          </p>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="feature-section-card">
      <template #header>
        <div class="section-head">
          <el-icon class="section-icon"><UploadFilled /></el-icon>
          <span>数据集上传与处理</span>
        </div>
      </template>

      <el-form label-position="top">
        <el-row :gutter="14">
          <el-col :xs="24" :sm="12" :md="11">
            <el-form-item label="数据集名称">
              <el-input v-model="form.name" placeholder="可选，不填默认使用文件名" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="13">
            <el-form-item label="上传文件（CSV / Excel / JSON）" class="dataset-upload-item">
              <div class="dataset-upload-box">
                <el-upload
                  ref="uploadRef"
                  :show-file-list="false"
                  :auto-upload="false"
                  :limit="1"
                  accept=".csv,.xls,.xlsx,.json"
                  :on-change="handleFileChange"
                  :on-exceed="handleFileExceed"
                >
                  <el-button type="primary" plain>选择文件</el-button>
                </el-upload>
                <div class="dataset-file-name" :class="{ empty: !fileState.fileName }">
                  {{ fileState.fileName || "未选择文件" }}
                </div>
              </div>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="层级字段">
              <el-input v-model="form.hierarchy_fields" placeholder="可选，例如：类别,厂商,车型" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="数值字段">
              <el-input v-model="form.value_field" placeholder="可选，例如：销量" />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="actions">
          <el-button type="primary" :loading="uploading" @click="handleUpload">
            上传并处理
          </el-button>
          <el-button @click="clearFile">清空文件</el-button>
        </div>
      </el-form>
    </el-card>

    <el-card v-if="summary" shadow="never" class="feature-section-card">
      <template #header>
        <div class="section-head">
          <el-icon class="section-icon"><DataAnalysis /></el-icon>
          <span>处理摘要</span>
        </div>
      </template>
      <el-row :gutter="12">
        <el-col :xs="24" :sm="8">
          <el-statistic title="原始行数" :value="summary.raw_rows || 0" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-statistic title="清洗后行数" :value="summary.clean_rows || 0" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-statistic title="树节点数" :value="summary.node_count || 0" />
        </el-col>
      </el-row>
      <div class="summary-actions">
        <el-button type="primary" plain @click="handlePreviewLatest">预览本次上传数据</el-button>
      </div>
    </el-card>

    <el-card shadow="never" class="feature-section-card">
      <template #header>
        <div class="section-head">
          <el-icon class="section-icon"><CollectionTag /></el-icon>
          <span>我的数据集</span>
        </div>
      </template>
      <el-table :data="datasets" v-loading="loading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" min-width="170" />
        <el-table-column prop="source_type" label="来源" width="110" />
        <el-table-column prop="total_rows" label="记录数" width="110" />
        <el-table-column prop="clean_status" label="清洗状态" width="120" />
        <el-table-column prop="created_at" label="创建时间" min-width="180" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handlePreview(row)">预览</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="previewDialog.visible"
      :title="previewDialog.title || '数据集预览'"
      width="82%"
      top="6vh"
      destroy-on-close
      @closed="handlePreviewDialogClosed"
    >
      <div class="dataset-preview-meta">
        <span>总行数：{{ previewDialog.totalRows }}</span>
        <span>当前预览：{{ previewDialog.previewCount }} 行</span>
      </div>
      <el-table :data="previewDialog.rows" border height="460" v-loading="previewLoading">
        <el-table-column type="index" label="#" width="64" />
        <el-table-column
          v-for="column in previewDialog.columns"
          :key="column"
          :prop="column"
          :label="column"
          min-width="140"
          show-overflow-tooltip
        />
      </el-table>
      <el-divider content-position="left">预处理节点预览</el-divider>
      <div class="dataset-preview-meta">
        <span>节点总数：{{ previewDialog.processedTotalRows }}</span>
        <span>当前预览：{{ previewDialog.processedPreviewCount }} 行</span>
      </div>
      <el-table :data="previewDialog.processedRows" border height="360" v-loading="previewLoading">
        <el-table-column type="index" label="#" width="64" />
        <el-table-column
          v-for="column in previewDialog.processedColumns"
          :key="`processed-${column}`"
          :prop="column"
          :label="column"
          min-width="140"
          show-overflow-tooltip
        />
      </el-table>
    </el-dialog>
  </div>
</template>
