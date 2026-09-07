<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import { DataAnalysis, Grid, SetUp } from "@element-plus/icons-vue";

import { fetchAnalysisFeatures, fetchAnalysisPca, fetchTreemapLayout } from "../../api/dataflow/analysis";
import { fetchDatasets } from "../../api/dataflow/dataset";

const STYLE_PRESETS = {
  clear: { topN: 60, minRatio: 0.8, padding: 3 },
  balanced: { topN: 120, minRatio: 0.3, padding: 2 },
  detail: { topN: 240, minRatio: 0.2, padding: 1 },
};

const loading = ref(false);
const pcaLoading = ref(false);
const datasets = ref([]);
const features = ref(null);
const allNodes = ref([]);
const layoutMeta = ref(null);
const pcaResult = ref(null);

const stylePreset = ref("clear");
const viewMode = ref("global");
const displayMode = ref("leaf");
const selectedLevel = ref(0);
const focusTrail = ref([0]);

const form = reactive({
  datasetId: "",
  width: 1080,
  height: 620,
  padding: STYLE_PRESETS.clear.padding,
  topN: STYLE_PRESETS.clear.topN,
  minRatio: STYLE_PRESETS.clear.minRatio,
});
const pcaForm = reactive({
  maxRows: 300,
  maxFeatures: 6,
});

const palette = ["#8ab5f5", "#6f9fe8", "#5b8cd9", "#4f82cd", "#3f71ba", "#3565a8"];

const canvasStyle = computed(() => ({
  width: `${form.width}px`,
  height: `${form.height}px`,
}));

const nodeMap = computed(() => {
  const map = new Map();
  for (const node of allNodes.value) {
    map.set(Number(node.id), node);
  }
  return map;
});

const childCountMap = computed(() => {
  const map = new Map();
  for (const node of allNodes.value) {
    const parentId = normalizeId(node.parent_id);
    if (parentId === null) {
      continue;
    }
    map.set(parentId, (map.get(parentId) || 0) + 1);
  }
  return map;
});

const parentIdSet = computed(() => {
  const set = new Set();
  for (const node of allNodes.value) {
    const parentId = normalizeId(node.parent_id);
    if (parentId !== null) {
      set.add(parentId);
    }
  }
  return set;
});

const leafNodes = computed(() => allNodes.value.filter((node) => !parentIdSet.value.has(Number(node.id))));

const levelOptions = computed(() =>
  [...new Set(allNodes.value.map((node) => Number(node.level || 0)))].sort((a, b) => a - b)
);

const globalVisibleNodes = computed(() => {
  if (displayMode.value === "leaf") {
    return [...leafNodes.value].sort((a, b) => Number(b.value_num || 0) - Number(a.value_num || 0));
  }
  return allNodes.value
    .filter((node) => Number(node.level) === Number(selectedLevel.value))
    .sort((a, b) => Number(b.value_num || 0) - Number(a.value_num || 0));
});

const currentFocusId = computed(() => focusTrail.value[focusTrail.value.length - 1] || 0);

const focusBreadcrumb = computed(() =>
  focusTrail.value.map((id) => {
    if (id === 0) {
      return { id: 0, label: "Root" };
    }
    return { id, label: nodeMap.value.get(id)?.node_name || `#${id}` };
  })
);

const structureWarning = computed(() => {
  if (!features.value) {
    return "";
  }
  const levelCount = Number(features.value.level_count || 0);
  const singleChildRatio = Number(features.value.single_child_parent_ratio || 0);
  if (levelCount <= 2 && singleChildRatio >= 0.75) {
    return "当前层级结构可能偏扁平，建议检查层级字段是否拆分正确（例如“厂商/车型”应拆成两级字段）。";
  }
  return "";
});

const activeRenderNodes = computed(() => {
  if (viewMode.value === "global") {
    return globalVisibleNodes.value.map((node) => toRenderNode(node));
  }
  return buildDrillRenderNodes();
});

const renderNodes = computed(() => {
  const nodes = activeRenderNodes.value;
  const priorityIds = new Set(
    [...nodes]
      .sort((a, b) => nodeArea(b) - nodeArea(a))
      .slice(0, 24)
      .map((node) => Number(node.id))
  );
  return nodes.map((node) => ({
    ...node,
    label: buildLabelModel(node, priorityIds),
  }));
});

const topLevelNodes = computed(() => allNodes.value.filter((node) => normalizeId(node.parent_id) === null));

const visibleValueTotal = computed(() =>
  activeRenderNodes.value.reduce((sum, node) => sum + Number(node.value_num || 0), 0)
);

const topReadableRows = computed(() =>
  [...activeRenderNodes.value]
    .sort((a, b) => Number(b.value_num || 0) - Number(a.value_num || 0))
    .slice(0, 15)
    .map((node, index) => {
      const value = Number(node.value_num || 0);
      const total = Number(visibleValueTotal.value || 0);
      const ratio = total > 0 ? (value / total) * 100 : 0;
      return {
        rank: index + 1,
        id: node.id,
        name: node.node_name,
        value: value,
        ratio: ratio,
      };
    })
);

const pcaPlotPoints = computed(() => {
  const points = Array.isArray(pcaResult.value?.points) ? pcaResult.value.points : [];
  if (!points.length) {
    return [];
  }

  const renderLimit = Math.min(points.length, 320);
  const sampled = points.slice(0, renderLimit);
  const xs = sampled.map((item) => Number(item.pc1 || 0));
  const ys = sampled.map((item) => Number(item.pc2 || 0));
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const rangeX = Math.max(maxX - minX, 1e-9);
  const rangeY = Math.max(maxY - minY, 1e-9);

  return sampled.map((item, index) => {
    const x = ((Number(item.pc1 || 0) - minX) / rangeX) * 88 + 6;
    const y = 94 - ((Number(item.pc2 || 0) - minY) / rangeY) * 88;
    return {
      ...item,
      dotId: `${item.index || index}-${index}`,
      x: Number(x.toFixed(2)),
      y: Number(y.toFixed(2)),
    };
  });
});

const pcaVarianceSummary = computed(() => {
  const ratios = pcaResult.value?.explained_variance_ratio || [0, 0];
  const pc1 = Number(ratios[0] || 0);
  const pc2 = Number(ratios[1] || 0);
  return {
    pc1,
    pc2,
    total: pc1 + pc2,
  };
});

function normalizeId(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  const id = Number(value);
  return Number.isFinite(id) ? id : null;
}

function toRenderNode(node) {
  return {
    ...node,
    draw_x: Number(node.x || 0),
    draw_y: Number(node.y || 0),
    draw_width: Number(node.width || 0),
    draw_height: Number(node.height || 0),
  };
}

function nodeArea(node) {
  return Math.max(Number(node.draw_width || 0), 0) * Math.max(Number(node.draw_height || 0), 0);
}

function buildLabelModel(node, priorityIds) {
  const width = Number(node.draw_width || 0);
  const height = Number(node.draw_height || 0);
  const area = nodeArea(node);
  const forceLabel = priorityIds.has(Number(node.id));

  if (width >= 120 && height >= 54) {
    return {
      variant: "full",
      vertical: false,
      name: node.node_name,
      value: formatNumber(node.value_num),
    };
  }

  if (width >= 76 && height >= 30) {
    return {
      variant: "compact",
      vertical: false,
      name: truncateText(node.node_name, 8),
      value: formatNumber(node.value_num),
    };
  }

  if (forceLabel || area >= 1500 || (width >= 22 && height >= 62)) {
    const vertical = width < 34 && height >= 70;
    return {
      variant: "mini",
      vertical,
      name: truncateText(node.node_name, vertical ? 4 : 6),
      value: formatNumber(node.value_num),
    };
  }

  return {
    variant: "none",
    vertical: false,
    name: "",
    value: "",
  };
}

function truncateText(text, maxLength) {
  const raw = String(text || "");
  if (raw.length <= maxLength) {
    return raw;
  }
  return `${raw.slice(0, maxLength)}...`;
}

function getChildrenByParentId(parentId) {
  if (parentId === 0) {
    return topLevelNodes.value;
  }
  return allNodes.value.filter((node) => normalizeId(node.parent_id) === Number(parentId));
}

function buildDrillRenderNodes() {
  const focusId = Number(currentFocusId.value || 0);
  const children = getChildrenByParentId(focusId);
  if (!children.length) {
    return [];
  }

  const focusRect = getFocusRect(focusId);
  if (focusRect.width <= 0 || focusRect.height <= 0) {
    return [];
  }

  const sx = form.width / focusRect.width;
  const sy = form.height / focusRect.height;
  return [...children]
    .sort((a, b) => Number(b.value_num || 0) - Number(a.value_num || 0))
    .map((node) => {
      const x = (Number(node.x || 0) - focusRect.x) * sx;
      const y = (Number(node.y || 0) - focusRect.y) * sy;
      const width = Number(node.width || 0) * sx;
      const height = Number(node.height || 0) * sy;
      return {
        ...node,
        draw_x: x,
        draw_y: y,
        draw_width: width,
        draw_height: height,
      };
    });
}

function getFocusRect(focusId) {
  if (focusId === 0) {
    return {
      x: 0,
      y: 0,
      width: Number(form.width || 0),
      height: Number(form.height || 0),
    };
  }
  const focusNode = nodeMap.value.get(Number(focusId));
  if (!focusNode) {
    return {
      x: 0,
      y: 0,
      width: Number(form.width || 0),
      height: Number(form.height || 0),
    };
  }
  return {
    x: Number(focusNode.x || 0),
    y: Number(focusNode.y || 0),
    width: Number(focusNode.width || 0),
    height: Number(focusNode.height || 0),
  };
}

function canDrill(node) {
  return (childCountMap.value.get(Number(node.id)) || 0) > 0;
}

function jumpToBreadcrumb(id) {
  if (id === 0) {
    focusTrail.value = [0];
    return;
  }
  focusTrail.value = buildPathToNode(id);
}

function buildPathToNode(targetId) {
  const path = [];
  let cursorId = Number(targetId);
  while (Number.isFinite(cursorId)) {
    path.unshift(cursorId);
    const current = nodeMap.value.get(cursorId);
    if (!current) {
      break;
    }
    const parentId = normalizeId(current.parent_id);
    if (parentId === null) {
      break;
    }
    cursorId = parentId;
  }
  return [0, ...path];
}

function handleNodeClick(node) {
  if (!canDrill(node)) {
    return;
  }
  viewMode.value = "drill";
  focusTrail.value = buildPathToNode(Number(node.id));
}

function goDrillUp() {
  if (focusTrail.value.length <= 1) {
    return;
  }
  focusTrail.value = focusTrail.value.slice(0, -1);
}

function resetDrill() {
  focusTrail.value = [0];
}

function nodeStyle(node) {
  const level = Number(node.level || 0);
  const alpha = viewMode.value === "drill" ? 0.94 : displayMode.value === "leaf" ? 0.96 : 0.88;
  return {
    left: `${Math.max(node.draw_x, 0)}px`,
    top: `${Math.max(node.draw_y, 0)}px`,
    width: `${Math.max(node.draw_width, 0)}px`,
    height: `${Math.max(node.draw_height, 0)}px`,
    backgroundColor: hexToRgba(palette[level % palette.length], alpha),
  };
}

function showDrillHint(node) {
  return canDrill(node) && node.draw_width > 130 && node.draw_height > 58;
}

function nodeTitle(node) {
  const childCount = childCountMap.value.get(Number(node.id)) || 0;
  const hint = childCount > 0 ? `\n可下钻子节点数：${childCount}` : "";
  return `节点：${node.node_name}\n值：${formatNumber(node.value_num)}\n层级：${node.level}${hint}`;
}

function formatNumber(value) {
  const num = Number(value || 0);
  if (!Number.isFinite(num)) {
    return "0";
  }
  return num.toLocaleString("zh-CN", { maximumFractionDigits: 4 });
}

function toPercent(value) {
  return `${Number(value || 0).toFixed(2)}%`;
}

function formatSigned(value) {
  const num = Number(value || 0);
  if (!Number.isFinite(num)) {
    return "0.0000";
  }
  return `${num >= 0 ? "+" : ""}${num.toFixed(4)}`;
}

function hexToRgba(hex, alpha) {
  const normalized = String(hex || "").replace("#", "");
  if (normalized.length !== 6) {
    return hex;
  }
  const r = parseInt(normalized.slice(0, 2), 16);
  const g = parseInt(normalized.slice(2, 4), 16);
  const b = parseInt(normalized.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

function applyStylePreset(presetKey) {
  const preset = STYLE_PRESETS[presetKey] || STYLE_PRESETS.clear;
  form.topN = preset.topN;
  form.minRatio = preset.minRatio;
  form.padding = preset.padding;
}

async function loadDatasets() {
  const result = await fetchDatasets(1, 100);
  datasets.value = result?.data || [];
  if (!form.datasetId && datasets.value.length > 0) {
    form.datasetId = String(datasets.value[0].id);
  }
}

async function runAnalysis() {
  if (!form.datasetId) {
    ElMessage.warning("请先选择数据集");
    return;
  }

  loading.value = true;
  try {
    const datasetId = Number(form.datasetId);
    const [featureResult, treemapResult] = await Promise.all([
      fetchAnalysisFeatures(datasetId),
      fetchTreemapLayout(
        datasetId,
        form.width,
        form.height,
        form.padding,
        form.topN,
        form.minRatio / 100
      ),
    ]);
    features.value = featureResult?.data?.features || null;
    allNodes.value = treemapResult?.data?.nodes || [];
    layoutMeta.value = treemapResult?.data?.layout_meta || null;

    const levels = levelOptions.value;
    selectedLevel.value = levels.length > 0 ? levels[0] : 0;
    displayMode.value = "leaf";
    viewMode.value = "global";
    focusTrail.value = [0];

    ElMessage.success("Treemap 生成完成");
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loading.value = false;
  }
}

async function runPcaAnalysis() {
  if (!form.datasetId) {
    ElMessage.warning("请先选择数据集");
    return;
  }

  pcaLoading.value = true;
  try {
    const datasetId = Number(form.datasetId);
    const result = await fetchAnalysisPca(datasetId, pcaForm.maxRows, pcaForm.maxFeatures);
    pcaResult.value = result?.data?.pca || null;
    if (!pcaResult.value) {
      throw new Error("PCA 返回结果为空");
    }
    ElMessage.success("PCA 降维分析完成");
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    pcaLoading.value = false;
  }
}

onMounted(async () => {
  applyStylePreset(stylePreset.value);
  try {
    await loadDatasets();
  } catch (error) {
    ElMessage.error(error.message);
  }
});
</script>

<template>
  <div class="page-wrap feature-page">
    <el-card shadow="never" class="feature-hero-card">
      <div class="feature-hero-head">
        <div>
          <h2>Treemap 分析</h2>
          <p>
            当节点过多时，小块会自然变细。当前页面提供“样式预设 + 自适应标签 + Top榜单”，保证小块场景也能读到核心信息。
          </p>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="feature-section-card">
      <template #header>
        <div class="section-head">
          <el-icon class="section-icon"><SetUp /></el-icon>
          <span>Treemap 参数设置</span>
        </div>
      </template>
      <el-form label-position="top">
        <el-row :gutter="12">
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="数据集">
              <el-select v-model="form.datasetId" placeholder="请选择数据集">
                <el-option
                  v-for="item in datasets"
                  :key="item.id"
                  :label="`${item.name}（ID:${item.id}）`"
                  :value="String(item.id)"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-form-item label="显示预设">
              <el-radio-group v-model="stylePreset" size="small" @change="applyStylePreset">
                <el-radio-button value="clear">清晰优先</el-radio-button>
                <el-radio-button value="balanced">平衡模式</el-radio-button>
                <el-radio-button value="detail">细节模式</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="4">
            <el-form-item label="宽度">
              <el-input-number v-model="form.width" :min="200" :max="2400" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="4">
            <el-form-item label="高度">
              <el-input-number v-model="form.height" :min="200" :max="1400" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="4">
            <el-form-item label="内边距">
              <el-input-number v-model="form.padding" :min="0" :max="12" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="4">
            <el-form-item label="TopN（每层）">
              <el-input-number v-model="form.topN" :min="0" :max="500" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="4">
            <el-form-item label="最小占比(%)">
              <el-input-number v-model="form.minRatio" :min="0" :max="20" :step="0.1" :precision="1" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12" :md="4">
            <el-form-item label="操作">
              <el-button type="primary" :loading="loading" @click="runAnalysis">生成布局</el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>

    <el-card v-if="features" shadow="never" class="feature-section-card">
      <template #header>
        <div class="section-head">
          <el-icon class="section-icon"><DataAnalysis /></el-icon>
          <span>结构诊断</span>
        </div>
      </template>
      <el-row :gutter="12">
        <el-col :xs="24" :sm="8">
          <el-statistic title="总节点数" :value="features.total_nodes || 0" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-statistic title="叶子节点" :value="features.leaf_nodes || 0" />
        </el-col>
        <el-col :xs="24" :sm="8">
          <el-statistic title="层级数（不含Root）" :value="features.level_count || 0" />
        </el-col>
      </el-row>
      <el-row :gutter="12" style="margin-top: 8px">
        <el-col :xs="24" :sm="12">
          <div class="treemap-metric-item">
            单子节点父节点占比：{{ toPercent((features.single_child_parent_ratio || 0) * 100) }}
          </div>
        </el-col>
        <el-col :xs="24" :sm="12">
          <div class="treemap-metric-item">
            平均分叉数：{{ Number(features.avg_branch_factor || 0).toFixed(2) }}
          </div>
        </el-col>
      </el-row>
      <el-alert
        v-if="structureWarning"
        type="warning"
        :title="structureWarning"
        :closable="false"
        show-icon
        class="treemap-structure-warning"
      />
    </el-card>

    <el-card shadow="never" class="feature-section-card">
      <template #header>
        <div class="section-head">
          <el-icon class="section-icon"><DataAnalysis /></el-icon>
          <span>PCA 降维（简化版）</span>
        </div>
      </template>

      <el-row :gutter="12" class="pca-toolbar">
        <el-col :xs="24" :sm="10" :md="7">
          <el-form-item label="样本上限">
            <el-input-number v-model="pcaForm.maxRows" :min="20" :max="2000" />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="10" :md="7">
          <el-form-item label="特征字段上限">
            <el-input-number v-model="pcaForm.maxFeatures" :min="2" :max="12" />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="24" :md="10" class="pca-run-cell">
          <el-button type="primary" :loading="pcaLoading" @click="runPcaAnalysis">运行 PCA</el-button>
        </el-col>
      </el-row>

      <div v-if="pcaResult" class="pca-layout">
        <div class="pca-left">
          <el-row :gutter="10">
            <el-col :xs="24" :sm="8">
              <el-statistic title="样本数" :value="pcaResult.sample_count || 0" />
            </el-col>
            <el-col :xs="24" :sm="8">
              <el-statistic title="PC1 方差贡献" :value="Number((pcaVarianceSummary.pc1 * 100).toFixed(2))" suffix="%" />
            </el-col>
            <el-col :xs="24" :sm="8">
              <el-statistic title="PC1+PC2 累计贡献" :value="Number((pcaVarianceSummary.total * 100).toFixed(2))" suffix="%" />
            </el-col>
          </el-row>

          <div class="pca-meta">
            使用字段：{{ (pcaResult.features || []).join("、") || "-" }}
            <span v-if="pcaResult.label_field">｜标签字段：{{ pcaResult.label_field }}</span>
          </div>

          <div class="pca-plot">
            <div class="pca-axis x"></div>
            <div class="pca-axis y"></div>
            <div
              v-for="point in pcaPlotPoints"
              :key="`pca-${point.dotId}`"
              class="pca-point"
              :style="{ left: `${point.x}%`, top: `${point.y}%` }"
              :title="`${point.label} ｜ PC1=${formatSigned(point.pc1)} ｜ PC2=${formatSigned(point.pc2)}`"
            ></div>
          </div>
          <div class="pca-plot-note">
            仅展示前 {{ pcaPlotPoints.length }} 个点（用于页面可读性），悬停点可查看标签与坐标。
          </div>
        </div>

        <div class="pca-right">
          <div class="pca-weight-title">主成分载荷（Top 10）</div>
          <el-table :data="pcaResult.component_weights || []" size="small" border height="280">
            <el-table-column prop="field" label="字段" min-width="120" />
            <el-table-column prop="pc1_weight" label="PC1 载荷" min-width="100" />
            <el-table-column prop="pc2_weight" label="PC2 载荷" min-width="100" />
            <el-table-column prop="pc_abs_sum" label="综合影响" min-width="100" />
          </el-table>
        </div>
      </div>
      <el-empty v-else description="点击“运行 PCA”后查看降维结果" :image-size="72" />
    </el-card>

    <el-card shadow="never" class="feature-section-card">
      <template #header>
        <div class="section-head">
          <el-icon class="section-icon"><Grid /></el-icon>
          <span>Treemap 结果</span>
        </div>
      </template>

      <div class="treemap-toolbar">
        <div class="treemap-toolbar-left">
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button value="global">全局视图</el-radio-button>
            <el-radio-button value="drill">下钻视图</el-radio-button>
          </el-radio-group>

          <template v-if="viewMode === 'global'">
            <el-radio-group v-model="displayMode" size="small">
              <el-radio-button value="leaf">叶子节点视图</el-radio-button>
              <el-radio-button value="level">按层级查看</el-radio-button>
            </el-radio-group>
            <el-select
              v-if="displayMode === 'level'"
              v-model="selectedLevel"
              size="small"
              style="width: 140px"
            >
              <el-option v-for="level in levelOptions" :key="level" :label="`层级 ${level}`" :value="level" />
            </el-select>
          </template>

          <template v-else>
            <el-breadcrumb separator="/" class="treemap-breadcrumb">
              <el-breadcrumb-item v-for="item in focusBreadcrumb" :key="item.id">
                <a href="#" @click.prevent="jumpToBreadcrumb(item.id)">{{ item.label }}</a>
              </el-breadcrumb-item>
            </el-breadcrumb>
            <el-button size="small" @click="goDrillUp" :disabled="focusTrail.length <= 1">返回上层</el-button>
            <el-button size="small" @click="resetDrill" :disabled="focusTrail.length <= 1">回到根节点</el-button>
          </template>
        </div>
        <div class="treemap-meta">
          当前显示节点：{{ renderNodes.length }}
          <span v-if="layoutMeta">，已聚合小节点：{{ layoutMeta.aggregated_nodes || 0 }}</span>
          <span v-if="layoutMeta?.hidden_other_nodes">，隐藏过细聚合块：{{ layoutMeta.hidden_other_nodes }}</span>
        </div>
      </div>

      <div class="treemap-canvas" :style="canvasStyle">
        <div
          v-for="node in renderNodes"
          :key="`${viewMode}-${displayMode}-${node.id}`"
          class="treemap-node"
          :class="{ drillable: canDrill(node) }"
          :style="nodeStyle(node)"
          :title="nodeTitle(node)"
          @click="handleNodeClick(node)"
        >
          <div
            v-if="node.label.variant !== 'none'"
            class="treemap-label"
            :class="[`variant-${node.label.variant}`, { vertical: node.label.vertical }]"
          >
            <template v-if="node.label.variant === 'full'">
              <div class="treemap-name">{{ node.label.name }}</div>
              <div class="treemap-value">{{ node.label.value }}</div>
              <div v-if="showDrillHint(node)" class="treemap-drill-hint">点击下钻</div>
            </template>
            <template v-else-if="node.label.variant === 'compact'">
              <div class="treemap-name compact">{{ node.label.name }}</div>
              <div class="treemap-value compact">{{ node.label.value }}</div>
            </template>
            <template v-else>
              <div class="treemap-mini-name">{{ node.label.name }}</div>
              <div class="treemap-mini-value">{{ node.label.value }}</div>
            </template>
          </div>
        </div>
        <div v-if="!renderNodes.length" class="treemap-empty">当前视图无可展示节点</div>
      </div>

      <div class="treemap-top-panel">
        <div class="treemap-top-title">当前视图 Top 15 节点</div>
        <div class="treemap-top-grid treemap-top-head">
          <span>排名</span>
          <span>名称</span>
          <span>销量/数值</span>
          <span>占比</span>
        </div>
        <div v-for="item in topReadableRows" :key="item.id" class="treemap-top-grid treemap-top-row">
          <span>{{ item.rank }}</span>
          <span class="name" :title="item.name">{{ item.name }}</span>
          <span>{{ formatNumber(item.value) }}</span>
          <span>{{ toPercent(item.ratio) }}</span>
        </div>
      </div>
    </el-card>
  </div>
</template>
