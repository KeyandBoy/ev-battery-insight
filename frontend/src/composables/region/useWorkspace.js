import { computed, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  compareRuns,
  deleteDataset,
  fetchDatasetPreview,
  fetchDatasets,
  fetchDatasetSummary,
  fetchRunDetail,
  fetchRuns,
  generateDataset,
  getRunExportUrl,
  runAnalysis,
  runBenchmark,
  uploadDataset
} from "../../api/region/client";

const datasets = ref([]);
const runs = ref([]);
const selectedDatasetId = ref(null);
const selectedRegion = ref(null);
const currentRunId = ref(null);
const statusMessage = ref("欢迎进入高维数据区域分析工作台。");
const datasetSummary = ref(null);
const comparisonResult = ref(null);
const benchmarkResult = ref(null);
const selectedCompareRunIds = ref([null, null]);
const benchmarkRepeats = ref(2);

const preview = reactive({
  columns: [],
  rows: []
});

const loading = reactive({
  generate: false,
  upload: false,
  analysis: false,
  benchmark: false,
  bootstrap: false
});

function defaultConfig() {
  return {
    preprocess: {
      labelColumn: "label",
      missingStrategy: "median",
      scaler: "standard",
      varianceThreshold: 0.01,
      correlationThreshold: 0.97,
      maxFeatures: 12
    },
    reduction: {
      method: "umap",
      nComponents: 2,
      neighbors: 15,
      minDist: 0.1,
      perplexity: 30,
      learningRate: 200,
      metric: "euclidean"
    },
    clustering: {
      method: "dbscan",
      eps: 0.85,
      minSamples: 8,
      clusters: 4,
      linkage: "ward",
      densityBandwidth: 0.75,
      metric: "euclidean"
    }
  };
}

const config = reactive(defaultConfig());
const analysisResult = ref(null);

const currentDataset = computed(() => datasets.value.find((item) => item.id === selectedDatasetId.value) || null);

const visualization = computed(
  () =>
    analysisResult.value?.visualization || {
      points: [],
      regions: [],
      regionLinks: [],
      voronoiPolygons: [],
      parallelCoordinates: { dimensions: [], records: [] },
      featureCorrelation: {}
    }
);

const parallelRecords = computed(() => {
  const records = visualization.value.parallelCoordinates?.records || [];
  if (selectedRegion.value === null) {
    return records;
  }
  return [...records].sort(
    (left, right) => Number(right.region === selectedRegion.value) - Number(left.region === selectedRegion.value)
  );
});

async function bootstrapWorkspace() {
  if (loading.bootstrap) {
    return;
  }
  try {
    loading.bootstrap = true;
    await refreshAll();
  } finally {
    loading.bootstrap = false;
  }
}

async function refreshAll() {
  try {
    datasets.value = await fetchDatasets();
    runs.value = await fetchRuns();
    if (!datasets.value.length) {
      clearDatasetBoundState();
      return;
    }

    const hasCurrent = datasets.value.some((item) => item.id === selectedDatasetId.value);
    if (!hasCurrent) {
      await chooseDataset(datasets.value[0].id);
    }
  } catch (error) {
    notifyError(error, "刷新数据失败");
  }
}

async function chooseDataset(datasetId, options = {}) {
  const { preserveAnalysis = false } = options;
  try {
    selectedDatasetId.value = Number(datasetId);
    selectedRegion.value = null;
    if (!preserveAnalysis) {
      clearAnalysisBoundState();
    }

    const [previewSettled, summarySettled] = await Promise.allSettled([
      fetchDatasetPreview(selectedDatasetId.value),
      fetchDatasetSummary(selectedDatasetId.value)
    ]);

    const previewResult = previewSettled.status === "fulfilled" ? previewSettled.value : null;
    const summaryResult = summarySettled.status === "fulfilled" ? summarySettled.value : null;

    if (previewResult) {
      preview.columns = previewResult.columns || [];
      preview.rows = previewResult.preview || [];
    } else {
      preview.columns = [];
      preview.rows = [];
      notifyError(previewSettled.reason, "读取数据集预览失败");
    }
    datasetSummary.value = summaryResult || null;

    const fallbackDataset =
      previewResult?.dataset ||
      datasets.value.find((item) => item.id === selectedDatasetId.value) ||
      summaryResult?.dataset ||
      null;

    const datasetName = fallbackDataset?.name || "当前数据集";
    const sampleCount = fallbackDataset?.sampleCount ?? fallbackDataset?.sample_count ?? preview.rows.length ?? 0;
    statusMessage.value = `已载入数据集 ${datasetName}，共 ${sampleCount} 条记录。`;
  } catch (error) {
    notifyError(error, "读取数据集失败");
  }
}

async function generateSampleDataset(datasetType) {
  try {
    loading.generate = true;
    const dataset = await generateDataset(datasetType);
    await refreshAll();
    await chooseDataset(dataset.id);
    statusMessage.value = `已生成数据集 ${dataset.name}`;
    ElMessage.success(statusMessage.value);
  } catch (error) {
    notifyError(error, "生成数据集失败");
  } finally {
    loading.generate = false;
  }
}

async function uploadCsvDataset({ name, description, labelColumn, file }) {
  if (!file) {
    ElMessage.warning("请先选择要上传的 CSV 文件。");
    return;
  }
  try {
    loading.upload = true;
    const formData = new FormData();
    formData.append("name", name || "");
    formData.append("description", description || "");
    formData.append("labelColumn", labelColumn || "label");
    formData.append("file", file);
    const dataset = await uploadDataset(formData);
    await refreshAll();
    await chooseDataset(dataset.id);
    statusMessage.value = `已上传数据集 ${dataset.name}`;
    ElMessage.success(statusMessage.value);
  } catch (error) {
    notifyError(error, "上传数据集失败");
  } finally {
    loading.upload = false;
  }
}

async function submitAnalysis() {
  if (!selectedDatasetId.value) {
    ElMessage.warning("请先选择数据集。");
    return;
  }
  try {
    loading.analysis = true;
    selectedRegion.value = null;
    analysisResult.value = await runAnalysis({
      datasetId: selectedDatasetId.value,
      preprocess: { ...config.preprocess },
      reduction: { ...config.reduction },
      clustering: { ...config.clustering }
    });
    currentRunId.value = analysisResult.value.runId;
    runs.value = await fetchRuns();
    statusMessage.value = `分析完成，运行编号 #${analysisResult.value.runId}`;
    ElMessage.success(statusMessage.value);
  } catch (error) {
    notifyError(error, "分析执行失败");
  } finally {
    loading.analysis = false;
  }
}

async function loadRunDetail(runId) {
  try {
    const run = await fetchRunDetail(runId);
    currentRunId.value = run.id;
    analysisResult.value = {
      runId: run.id,
      dataset: run.datasetSnapshot || { id: run.datasetId },
      preprocess: run.preprocessSummary || {},
      reduction: run.reductionMetrics || {},
      clustering: run.clusteringMetrics || {},
      quality: run.qualityMetrics || {},
      performance: run.performanceMetrics || {},
      visualization: run.visualization || {}
    };
    syncConfigFromRun(run);
    if (run.datasetId) {
      await chooseDataset(run.datasetId, { preserveAnalysis: true });
    }
    statusMessage.value = `已加载运行 #${run.id}`;
    ElMessage.success(statusMessage.value);
  } catch (error) {
    notifyError(error, "加载运行详情失败");
  }
}

async function executeRunComparison() {
  const runIds = selectedCompareRunIds.value.filter(Boolean);
  if (runIds.length < 2) {
    ElMessage.warning("请选择两个运行记录进行对比。");
    return;
  }
  try {
    comparisonResult.value = await compareRuns(runIds);
    statusMessage.value = `已完成运行对比：#${comparisonResult.value.left.id} vs #${comparisonResult.value.right.id}`;
    ElMessage.success(statusMessage.value);
  } catch (error) {
    notifyError(error, "运行对比失败");
  }
}

async function executeBenchmark() {
  if (!selectedDatasetId.value) {
    ElMessage.warning("请先选择数据集，再运行基准测试。");
    return;
  }
  try {
    loading.benchmark = true;
    benchmarkResult.value = await runBenchmark({
      datasetId: selectedDatasetId.value,
      repeats: benchmarkRepeats.value,
      preprocess: { ...config.preprocess },
      reduction: { ...config.reduction },
      clustering: { ...config.clustering }
    });
    statusMessage.value = `基准测试完成，共执行 ${benchmarkResult.value.scenarioCount} 个场景。`;
    ElMessage.success(statusMessage.value);
  } catch (error) {
    notifyError(error, "基准测试失败");
  } finally {
    loading.benchmark = false;
  }
}

function resetConfig() {
  const defaults = defaultConfig();
  Object.assign(config.preprocess, defaults.preprocess);
  Object.assign(config.reduction, defaults.reduction);
  Object.assign(config.clustering, defaults.clustering);
  statusMessage.value = "分析参数已重置为默认值。";
  ElMessage.success(statusMessage.value);
}

function syncConfigFromRun(run) {
  const defaults = defaultConfig();
  Object.assign(config.preprocess, defaults.preprocess, run.preprocessConfig || {});
  Object.assign(config.reduction, defaults.reduction, run.algorithmConfig?.reduction || {});
  Object.assign(config.clustering, defaults.clustering, run.algorithmConfig?.clustering || {});
}

function setSelectedRegion(regionId) {
  selectedRegion.value = regionId;
}

function clearDatasetBoundState() {
  selectedDatasetId.value = null;
  datasetSummary.value = null;
  preview.columns = [];
  preview.rows = [];
  clearAnalysisBoundState();
}

function clearAnalysisBoundState() {
  analysisResult.value = null;
  currentRunId.value = null;
  benchmarkResult.value = null;
  comparisonResult.value = null;
  selectedCompareRunIds.value = [null, null];
}

function exportCurrentRun(format = "json") {
  if (!currentRunId.value) {
    ElMessage.warning("当前没有可导出的运行结果。");
    return;
  }
  window.open(getRunExportUrl(currentRunId.value, format), "_blank", "noopener,noreferrer");
}

async function removeDataset(datasetId) {
  try {
    const result = await deleteDataset(datasetId);
    if (selectedDatasetId.value === datasetId) {
      clearDatasetBoundState();
    }
    await refreshAll();
    statusMessage.value = `已删除数据集，同时清除 ${result.runsDeleted} 条关联运行记录。`;
    ElMessage.success(statusMessage.value);
  } catch (error) {
    notifyError(error, "删除数据集失败");
  }
}

function notifyError(error, fallback) {
  statusMessage.value = getErrorMessage(error, fallback);
  ElMessage.error(statusMessage.value);
}

function getErrorMessage(error, fallback) {
  return error?.response?.data?.message || error?.message || fallback;
}

export function useWorkspace() {
  return {
    datasets,
    runs,
    selectedDatasetId,
    selectedRegion,
    currentRunId,
    statusMessage,
    datasetSummary,
    comparisonResult,
    benchmarkResult,
    selectedCompareRunIds,
    benchmarkRepeats,
    preview,
    loading,
    config,
    analysisResult,
    currentDataset,
    visualization,
    parallelRecords,
    bootstrapWorkspace,
    refreshAll,
    chooseDataset,
    generateSampleDataset,
    uploadCsvDataset,
    submitAnalysis,
    loadRunDetail,
    executeRunComparison,
    executeBenchmark,
    resetConfig,
    syncConfigFromRun,
    setSelectedRegion,
    exportCurrentRun,
    removeDataset
  };
}
