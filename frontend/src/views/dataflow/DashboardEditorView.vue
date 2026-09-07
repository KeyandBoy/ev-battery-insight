<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { onBeforeRouteLeave } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { CollectionTag, DataAnalysis, SetUp } from "@element-plus/icons-vue";

import {
  createDashboard,
  deleteDashboard,
  fetchDashboardDetail,
  fetchDashboards,
  publishDashboard,
  saveDashboardLayout,
  updateDashboard,
} from "../../api/dataflow/dashboard";
import { fetchDatasetPreview, fetchDatasets } from "../../api/dataflow/dataset";

const COMPONENT_LIBRARY = [
  {
    type: "treemap",
    name: "Treemap",
    desc: "层级占比分析",
    w: 460,
    h: 320,
  },
  {
    type: "bar",
    name: "柱状图",
    desc: "分类对比分析",
    w: 420,
    h: 280,
  },
  {
    type: "line",
    name: "折线图",
    desc: "趋势分析",
    w: 420,
    h: 280,
  },
  {
    type: "pie",
    name: "饼图",
    desc: "结构占比分析",
    w: 360,
    h: 280,
  },
  {
    type: "table",
    name: "表格",
    desc: "明细数据呈现",
    w: 520,
    h: 300,
  },
];

const TYPE_LABEL = {
  treemap: "Treemap",
  bar: "柱状图",
  line: "折线图",
  pie: "饼图",
  table: "表格",
};

const MIN_COMP_W = 120;
const MIN_COMP_H = 80;
const DEFAULT_PREVIEW_COLOR = "#3f79ce";
const DEFAULT_BAR_VALUES = [35, 54, 76, 48, 66];
const DEFAULT_LINE_POINTS = [
  { x: 0, y: 78 },
  { x: 20, y: 42 },
  { x: 42, y: 56 },
  { x: 60, y: 30 },
  { x: 78, y: 46 },
  { x: 100, y: 22 },
];
const DEFAULT_PIE_SLICES = [
  { label: "A", value: 40 },
  { label: "B", value: 28 },
  { label: "C", value: 32 },
];
const DEFAULT_TABLE_ROWS = ["地区 A", "地区 B", "地区 C", "地区 D"];
const DEFAULT_TREEMAP_WEIGHTS = [34, 20, 17, 14, 15];

const dashboardList = ref([]);
const datasetList = ref([]);
const datasetPreviewMap = reactive({});
const datasetPreviewLoadingMap = reactive({});
const dashboardSelectId = ref(null);
const currentDashboardId = ref(null);
const currentDashboard = ref(null);
const selectedUid = ref("");

const loading = reactive({
  dashboards: false,
  detail: false,
  datasets: false,
  saving: false,
});

const createDialog = reactive({
  visible: false,
  submitting: false,
});

const createForm = reactive({
  name: "",
  description: "",
  canvas_width: 1920,
  canvas_height: 1080,
  theme: "light",
});

const dataPreviewDialog = reactive({
  visible: false,
  datasetName: "",
  columns: [],
  rows: [],
  totalRows: 0,
  previewCount: 0,
});

const bindingAssistantDialog = reactive({
  visible: false,
});

const componentForm = reactive({
  title: "",
  dataset_id: null,
  x: 0,
  y: 0,
  w: 320,
  h: 220,
  z_index: 1,
  locked: false,
  color: DEFAULT_PREVIEW_COLOR,
  bar_values_text: "",
  line_points_text: "",
  pie_slices_text: "",
  table_rows_text: "",
  treemap_weights_text: "",
  binding_category_field: "",
  binding_value_field: "",
  binding_x_field: "",
  binding_y_field: "",
  binding_series_field: "",
  binding_json_text: "{}",
});

const editor = reactive({
  canvasWidth: 1920,
  canvasHeight: 1080,
  theme: "light",
  zoom: 70,
  showGrid: true,
  snapEnabled: true,
  snapSize: 20,
  isDirty: false,
  components: [],
});

const interaction = reactive({
  mode: "",
  targetUid: "",
  startX: 0,
  startY: 0,
  originX: 0,
  originY: 0,
  originW: 0,
  originH: 0,
  changed: false,
});

const historyState = reactive({
  stack: [],
  index: -1,
  mute: false,
  max: 120,
});

let localUidSeed = Date.now();
const savedLayoutSnapshot = ref("");

const selectedComponent = computed(() =>
  editor.components.find((item) => item.uid === selectedUid.value) || null
);

const publishStatus = computed(() => Boolean(currentDashboard.value?.is_published));
const publishStatusText = computed(() => (publishStatus.value ? "已发布" : "未发布"));
const publishStatusTagType = computed(() => (publishStatus.value ? "success" : "info"));
const canvasThemeClass = computed(() => {
  const theme = String(editor.theme || "light").toLowerCase();
  if (theme === "dark") {
    return "theme-dark";
  }
  if (theme === "tech-blue") {
    return "theme-tech";
  }
  return "theme-light";
});

const sortedComponents = computed(() =>
  [...editor.components].sort((a, b) => Number(a.z_index || 0) - Number(b.z_index || 0))
);

const canvasScale = computed(() => clampNumber(Number(editor.zoom || 100), 30, 180) / 100);

const canvasStageStyle = computed(() => ({
  width: `${Math.round(editor.canvasWidth * canvasScale.value)}px`,
  height: `${Math.round(editor.canvasHeight * canvasScale.value)}px`,
}));

const canvasStyle = computed(() => ({
  width: `${editor.canvasWidth}px`,
  height: `${editor.canvasHeight}px`,
  transform: `scale(${canvasScale.value})`,
  transformOrigin: "left top",
}));

const gridStyle = computed(() => {
  const size = clampNumber(Number(editor.snapSize || 20), 4, 200);
  return {
    backgroundSize: `${size}px ${size}px`,
  };
});

const canUndo = computed(() => historyState.index > 0);
const canRedo = computed(() => historyState.index >= 0 && historyState.index < historyState.stack.length - 1);

const selectedDatasetPreviewState = computed(() => {
  const datasetId = Number(componentForm.dataset_id || selectedComponent.value?.dataset_id || 0);
  if (!datasetId) {
    return null;
  }
  return getDatasetPreviewState(datasetId);
});

const selectedDatasetFieldMeta = computed(() => {
  const state = selectedDatasetPreviewState.value;
  const rows = state?.rows || [];
  if (!rows.length) {
    return { fields: [], numericFields: [], dimensionFields: [] };
  }
  return detectDatasetFieldMeta(rows, state?.columns || []);
});

function clampNumber(value, min, max) {
  const num = Number(value);
  if (!Number.isFinite(num)) {
    return min;
  }
  if (num < min) {
    return min;
  }
  if (num > max) {
    return max;
  }
  return num;
}

function newUid() {
  localUidSeed += 1;
  return `local-${localUidSeed}`;
}

function normalizeType(type) {
  const normalized = String(type || "")
    .trim()
    .toLowerCase();
  return TYPE_LABEL[normalized] ? normalized : "bar";
}

function getTypeLabel(type) {
  return TYPE_LABEL[normalizeType(type)] || "组件";
}

function defaultTitleByType(type) {
  return `${getTypeLabel(type)}组件`;
}

function maxZIndex() {
  return editor.components.reduce((max, item) => Math.max(max, Number(item.z_index || 0)), 0);
}

function snapValue(value, force = false) {
  if (!force && !editor.snapEnabled) {
    return Math.round(Number(value || 0));
  }
  const step = clampNumber(Number(editor.snapSize || 20), 4, 200);
  return Math.round(Number(value || 0) / step) * step;
}

function normalizeComponentBounds(component, forceSnap = false) {
  const maxW = Math.max(MIN_COMP_W, editor.canvasWidth);
  const maxH = Math.max(MIN_COMP_H, editor.canvasHeight);
  component.w = clampNumber(component.w, MIN_COMP_W, maxW);
  component.h = clampNumber(component.h, MIN_COMP_H, maxH);

  let nextX = clampNumber(component.x, 0, Math.max(0, editor.canvasWidth - component.w));
  let nextY = clampNumber(component.y, 0, Math.max(0, editor.canvasHeight - component.h));
  if (editor.snapEnabled || forceSnap) {
    nextX = snapValue(nextX, true);
    nextY = snapValue(nextY, true);
    nextX = clampNumber(nextX, 0, Math.max(0, editor.canvasWidth - component.w));
    nextY = clampNumber(nextY, 0, Math.max(0, editor.canvasHeight - component.h));
  }
  component.x = Math.round(nextX);
  component.y = Math.round(nextY);
  component.w = Math.round(component.w);
  component.h = Math.round(component.h);
}

function normalizeAllComponents(forceSnap = false) {
  for (const item of editor.components) {
    normalizeComponentBounds(item, forceSnap);
  }
}

function normalizeZIndices() {
  const ordered = [...editor.components].sort((a, b) => Number(a.z_index || 0) - Number(b.z_index || 0));
  ordered.forEach((item, index) => {
    item.z_index = index + 1;
  });
}

function resetComponentForm() {
  componentForm.title = "";
  componentForm.dataset_id = null;
  componentForm.x = 0;
  componentForm.y = 0;
  componentForm.w = 320;
  componentForm.h = 220;
  componentForm.z_index = 1;
  componentForm.locked = false;
  componentForm.color = DEFAULT_PREVIEW_COLOR;
  componentForm.bar_values_text = DEFAULT_BAR_VALUES.join(", ");
  componentForm.line_points_text = DEFAULT_LINE_POINTS.map((item) => `${item.x},${item.y}`).join("; ");
  componentForm.pie_slices_text = DEFAULT_PIE_SLICES.map((item) => `${item.label}:${item.value}`).join(", ");
  componentForm.table_rows_text = DEFAULT_TABLE_ROWS.join("\n");
  componentForm.treemap_weights_text = DEFAULT_TREEMAP_WEIGHTS.join(", ");
  componentForm.binding_category_field = "";
  componentForm.binding_value_field = "";
  componentForm.binding_x_field = "";
  componentForm.binding_y_field = "";
  componentForm.binding_series_field = "";
  componentForm.binding_json_text = "{}";
}

function normalizePositiveInt(value, fallback, minimum = 1, maximum = 100) {
  const num = Number(value);
  if (!Number.isFinite(num)) {
    return fallback;
  }
  return Math.round(clampNumber(num, minimum, maximum));
}

function normalizePreviewConfig(componentType, inputConfig) {
  const config = inputConfig && typeof inputConfig === "object" ? inputConfig : {};
  const color = String(config.color || "").trim() || DEFAULT_PREVIEW_COLOR;
  const locked = config.locked === true || Number(config.locked) === 1;

  const barValuesInput = Array.isArray(config.bar_values) ? config.bar_values : DEFAULT_BAR_VALUES;
  const barValues = barValuesInput
    .map((value, index) => normalizePositiveInt(value, DEFAULT_BAR_VALUES[index] || 50, 8, 98))
    .slice(0, 5);
  while (barValues.length < 5) {
    barValues.push(DEFAULT_BAR_VALUES[barValues.length]);
  }

  const linePointsInput = Array.isArray(config.line_points) ? config.line_points : DEFAULT_LINE_POINTS;
  const linePoints = linePointsInput
    .map((item, index) => {
      const fallback = DEFAULT_LINE_POINTS[index] || DEFAULT_LINE_POINTS[DEFAULT_LINE_POINTS.length - 1];
      const x = normalizePositiveInt(item?.x, fallback.x, 0, 100);
      const y = normalizePositiveInt(item?.y, fallback.y, 0, 100);
      return { x, y };
    })
    .filter((item) => Number.isFinite(item.x) && Number.isFinite(item.y))
    .slice(0, 10);
  if (linePoints.length < 2) {
    return {
      color,
      locked: locked ? 1 : 0,
      bar_values: barValues,
      line_points: DEFAULT_LINE_POINTS,
      pie_slices: DEFAULT_PIE_SLICES,
      table_rows: DEFAULT_TABLE_ROWS,
      treemap_weights: DEFAULT_TREEMAP_WEIGHTS,
    };
  }

  const pieSlicesInput = Array.isArray(config.pie_slices) ? config.pie_slices : DEFAULT_PIE_SLICES;
  const pieSlices = pieSlicesInput
    .map((item, index) => {
      const label = String(item?.label || `分类${index + 1}`).trim() || `分类${index + 1}`;
      const value = normalizePositiveInt(item?.value, 10, 1, 1000);
      return { label: label.slice(0, 12), value };
    })
    .slice(0, 8);
  if (!pieSlices.length) {
    pieSlices.push(...DEFAULT_PIE_SLICES);
  }

  const tableRowsInput = Array.isArray(config.table_rows) ? config.table_rows : DEFAULT_TABLE_ROWS;
  const tableRows = tableRowsInput
    .map((item) => String(item || "").trim())
    .filter((item) => item)
    .slice(0, 8);
  if (!tableRows.length) {
    tableRows.push(...DEFAULT_TABLE_ROWS);
  }

  const treemapWeightsInput = Array.isArray(config.treemap_weights) ? config.treemap_weights : DEFAULT_TREEMAP_WEIGHTS;
  const treemapWeights = treemapWeightsInput
    .map((value, index) => normalizePositiveInt(value, DEFAULT_TREEMAP_WEIGHTS[index] || 10, 1, 100))
    .slice(0, 5);
  while (treemapWeights.length < 5) {
    treemapWeights.push(DEFAULT_TREEMAP_WEIGHTS[treemapWeights.length]);
  }

  if (componentType === "line") {
    linePoints.sort((a, b) => a.x - b.x);
  }

  return {
    color,
    locked: locked ? 1 : 0,
    bar_values: barValues,
    line_points: linePoints,
    pie_slices: pieSlices,
    table_rows: tableRows,
    treemap_weights: treemapWeights,
  };
}

function getPreviewConfig(component) {
  if (!component) {
    return normalizePreviewConfig("bar", {});
  }
  return normalizePreviewConfig(component.type, component.config_json);
}

function isComponentLocked(component) {
  if (!component) {
    return false;
  }
  return Number(getPreviewConfig(component).locked || 0) === 1;
}

function syncComponentForm(component) {
  if (!component) {
    resetComponentForm();
    return;
  }

  const previewConfig = getPreviewConfig(component);
  componentForm.title = String(component.title || defaultTitleByType(component.type));
  componentForm.dataset_id = component.dataset_id ?? null;
  componentForm.x = Number(component.x || 0);
  componentForm.y = Number(component.y || 0);
  componentForm.w = Number(component.w || 320);
  componentForm.h = Number(component.h || 220);
  componentForm.z_index = Number(component.z_index || 1);
  componentForm.locked = isComponentLocked(component);

  componentForm.color = previewConfig.color;
  componentForm.bar_values_text = previewConfig.bar_values.join(", ");
  componentForm.line_points_text = previewConfig.line_points.map((item) => `${item.x},${item.y}`).join("; ");
  componentForm.pie_slices_text = previewConfig.pie_slices.map((item) => `${item.label}:${item.value}`).join(", ");
  componentForm.table_rows_text = previewConfig.table_rows.join("\n");
  componentForm.treemap_weights_text = previewConfig.treemap_weights.join(", ");
  const bindingJson = component.binding_json && typeof component.binding_json === "object" ? component.binding_json : {};
  componentForm.binding_category_field = String(
    bindingJson.categoryField || bindingJson.category_field || bindingJson.nameField || bindingJson.name_field || ""
  );
  componentForm.binding_value_field = String(
    bindingJson.valueField || bindingJson.value_field || bindingJson.metric || ""
  );
  componentForm.binding_x_field = String(bindingJson.xField || bindingJson.x_field || "");
  componentForm.binding_y_field = String(bindingJson.yField || bindingJson.y_field || "");
  componentForm.binding_series_field = String(bindingJson.seriesField || bindingJson.series_field || "");
  componentForm.binding_json_text = JSON.stringify(bindingJson, null, 2);
  if (componentForm.dataset_id) {
    void ensureDatasetPreview(componentForm.dataset_id);
  }
}

function createEmptyEditorState() {
  editor.canvasWidth = 1920;
  editor.canvasHeight = 1080;
  editor.theme = "light";
  editor.zoom = 70;
  editor.showGrid = true;
  editor.snapEnabled = true;
  editor.snapSize = 20;
  editor.components = [];
  selectedUid.value = "";
  resetComponentForm();
  commitSavedSnapshot();
  resetHistory();
}

function toPersistComponent(item, index) {
  return {
    id: item.id || null,
    dataset_id: item.dataset_id || null,
    type: normalizeType(item.type),
    title: String(item.title || "").trim() || defaultTitleByType(item.type),
    x: Math.round(item.x),
    y: Math.round(item.y),
    w: Math.round(item.w),
    h: Math.round(item.h),
    z_index: Number(item.z_index || index + 1),
    config_json: item.config_json || {},
    binding_json: item.binding_json || {},
  };
}

function buildPersistSnapshot() {
  const payload = {
    canvas_width: editor.canvasWidth,
    canvas_height: editor.canvasHeight,
    theme: editor.theme,
    layout_json: {
      zoom: editor.zoom,
      show_grid: editor.showGrid ? 1 : 0,
      snap_enabled: editor.snapEnabled ? 1 : 0,
      snap_size: editor.snapSize,
    },
    components: [...editor.components]
      .sort((a, b) => Number(a.z_index || 0) - Number(b.z_index || 0))
      .map((item, index) => toPersistComponent(item, index)),
  };
  return JSON.stringify(payload);
}

function buildHistorySnapshot() {
  const payload = {
    canvasWidth: editor.canvasWidth,
    canvasHeight: editor.canvasHeight,
    theme: editor.theme,
    zoom: editor.zoom,
    showGrid: editor.showGrid,
    snapEnabled: editor.snapEnabled,
    snapSize: editor.snapSize,
    selectedUid: selectedUid.value,
    components: editor.components.map((item) => ({
      uid: item.uid,
      id: item.id || null,
      dataset_id: item.dataset_id || null,
      type: normalizeType(item.type),
      title: item.title || "",
      x: Number(item.x || 0),
      y: Number(item.y || 0),
      w: Number(item.w || 0),
      h: Number(item.h || 0),
      z_index: Number(item.z_index || 1),
      config_json: item.config_json || {},
      binding_json: item.binding_json || {},
    })),
  };
  return JSON.stringify(payload);
}

function restoreHistorySnapshot(snapshot) {
  let parsed = null;
  try {
    parsed = JSON.parse(snapshot);
  } catch {
    return;
  }

  historyState.mute = true;
  editor.canvasWidth = clampNumber(parsed.canvasWidth, 600, 4096);
  editor.canvasHeight = clampNumber(parsed.canvasHeight, 360, 2160);
  editor.theme = String(parsed.theme || "light");
  editor.zoom = clampNumber(parsed.zoom, 30, 180);
  editor.showGrid = parsed.showGrid !== false;
  editor.snapEnabled = parsed.snapEnabled !== false;
  editor.snapSize = clampNumber(parsed.snapSize, 4, 200);
  editor.components = (parsed.components || []).map((item, index) => ({
    uid: item.uid || newUid(),
    id: item.id || null,
    dataset_id: item.dataset_id || null,
    type: normalizeType(item.type),
    title: String(item.title || defaultTitleByType(item.type)),
    x: Number(item.x || 0),
    y: Number(item.y || 0),
    w: Number(item.w || 320),
    h: Number(item.h || 220),
    z_index: Number(item.z_index || index + 1),
    config_json: item.config_json || {},
    binding_json: item.binding_json || {},
  }));
  normalizeAllComponents(false);
  normalizeZIndices();
  selectedUid.value = parsed.selectedUid || "";
  if (!editor.components.some((item) => item.uid === selectedUid.value)) {
    selectedUid.value = "";
  }
  syncComponentForm(selectedComponent.value);
  historyState.mute = false;
  updateDirtyFlag();
}

function resetHistory() {
  historyState.mute = true;
  historyState.stack = [buildHistorySnapshot()];
  historyState.index = 0;
  historyState.mute = false;
}

function pushHistorySnapshot() {
  if (historyState.mute) {
    return;
  }
  const snapshot = buildHistorySnapshot();
  if (historyState.index >= 0 && historyState.stack[historyState.index] === snapshot) {
    return;
  }
  if (historyState.index < historyState.stack.length - 1) {
    historyState.stack = historyState.stack.slice(0, historyState.index + 1);
  }
  historyState.stack.push(snapshot);
  if (historyState.stack.length > historyState.max) {
    historyState.stack.shift();
  }
  historyState.index = historyState.stack.length - 1;
}

function updateDirtyFlag() {
  editor.isDirty = buildPersistSnapshot() !== savedLayoutSnapshot.value;
}

function commitSavedSnapshot() {
  savedLayoutSnapshot.value = buildPersistSnapshot();
  editor.isDirty = false;
}

function commitLayoutChange(pushHistory = true) {
  if (pushHistory) {
    pushHistorySnapshot();
  }
  updateDirtyFlag();
}
function buildComponentFromLibrary(type) {
  const normalizedType = normalizeType(type);
  const spec = COMPONENT_LIBRARY.find((item) => item.type === normalizedType) || COMPONENT_LIBRARY[0];
  const offset = editor.components.length * 18;
  const w = clampNumber(spec.w, MIN_COMP_W, editor.canvasWidth);
  const h = clampNumber(spec.h, MIN_COMP_H, editor.canvasHeight);
  let x = clampNumber(34 + offset, 0, Math.max(0, editor.canvasWidth - w));
  let y = clampNumber(34 + offset, 0, Math.max(0, editor.canvasHeight - h));
  if (editor.snapEnabled) {
    x = snapValue(x, true);
    y = snapValue(y, true);
  }
  return {
    uid: newUid(),
    id: null,
    dataset_id: null,
    type: normalizedType,
    title: defaultTitleByType(normalizedType),
    x,
    y,
    w,
    h,
    z_index: maxZIndex() + 1,
    config_json: {},
    binding_json: {},
  };
}

function addComponent(type) {
  if (!currentDashboardId.value) {
    ElMessage.warning("请先创建或选择一个大屏");
    return;
  }
  const component = buildComponentFromLibrary(type);
  editor.components.push(component);
  selectedUid.value = component.uid;
  normalizeZIndices();
  commitLayoutChange(true);
}

function selectComponent(uid) {
  selectedUid.value = uid;
}

function clearSelection() {
  selectedUid.value = "";
}

function removeSelectedComponent(fromKeyboard = false) {
  const target = selectedComponent.value;
  if (!target) {
    return;
  }
  if (isComponentLocked(target)) {
    ElMessage.warning("组件已锁定，请先解锁后删除");
    return;
  }
  editor.components = editor.components.filter((item) => item.uid !== target.uid);
  selectedUid.value = "";
  normalizeZIndices();
  commitLayoutChange(true);
  if (fromKeyboard) {
    ElMessage.success("组件已删除，可按 Ctrl+Z 撤销");
  }
}

function duplicateSelectedComponent() {
  const target = selectedComponent.value;
  if (!target) {
    ElMessage.warning("请先选择组件");
    return;
  }
  const copy = {
    ...target,
    uid: newUid(),
    id: null,
    title: `${target.title || defaultTitleByType(target.type)} 副本`,
    x: clampNumber(target.x + 24, 0, Math.max(0, editor.canvasWidth - target.w)),
    y: clampNumber(target.y + 24, 0, Math.max(0, editor.canvasHeight - target.h)),
    z_index: maxZIndex() + 1,
  };
  normalizeComponentBounds(copy, editor.snapEnabled);
  editor.components.push(copy);
  selectedUid.value = copy.uid;
  normalizeZIndices();
  commitLayoutChange(true);
}

function moveSelectedZ(forward) {
  const target = selectedComponent.value;
  if (!target) {
    return;
  }
  if (isComponentLocked(target)) {
    ElMessage.warning("组件已锁定，无法调整层级");
    return;
  }
  const ordered = [...editor.components].sort((a, b) => Number(a.z_index || 0) - Number(b.z_index || 0));
  const index = ordered.findIndex((item) => item.uid === target.uid);
  const swapIndex = forward ? index + 1 : index - 1;
  if (index < 0 || swapIndex < 0 || swapIndex >= ordered.length) {
    return;
  }
  const current = ordered[index];
  const swapped = ordered[swapIndex];
  const tempZ = current.z_index;
  current.z_index = swapped.z_index;
  swapped.z_index = tempZ;
  normalizeZIndices();
  commitLayoutChange(true);
}

function startMove(component, event) {
  if (event.button !== 0) {
    return;
  }
  if (isComponentLocked(component)) {
    return;
  }
  selectComponent(component.uid);
  interaction.mode = "move";
  interaction.targetUid = component.uid;
  interaction.startX = event.clientX;
  interaction.startY = event.clientY;
  interaction.originX = Number(component.x || 0);
  interaction.originY = Number(component.y || 0);
  interaction.originW = Number(component.w || 0);
  interaction.originH = Number(component.h || 0);
  interaction.changed = false;
  window.addEventListener("mousemove", onPointerMove);
  window.addEventListener("mouseup", stopPointerAction);
  event.preventDefault();
}

function startResize(component, event) {
  if (event.button !== 0) {
    return;
  }
  if (isComponentLocked(component)) {
    return;
  }
  selectComponent(component.uid);
  interaction.mode = "resize";
  interaction.targetUid = component.uid;
  interaction.startX = event.clientX;
  interaction.startY = event.clientY;
  interaction.originX = Number(component.x || 0);
  interaction.originY = Number(component.y || 0);
  interaction.originW = Number(component.w || 0);
  interaction.originH = Number(component.h || 0);
  interaction.changed = false;
  window.addEventListener("mousemove", onPointerMove);
  window.addEventListener("mouseup", stopPointerAction);
  event.preventDefault();
}

function onPointerMove(event) {
  if (!interaction.mode || !interaction.targetUid) {
    return;
  }
  const target = editor.components.find((item) => item.uid === interaction.targetUid);
  if (!target) {
    return;
  }
  const dx = (event.clientX - interaction.startX) / canvasScale.value;
  const dy = (event.clientY - interaction.startY) / canvasScale.value;

  if (interaction.mode === "move") {
    let nextX = interaction.originX + dx;
    let nextY = interaction.originY + dy;
    if (editor.snapEnabled && !event.altKey) {
      nextX = snapValue(nextX, true);
      nextY = snapValue(nextY, true);
    }
    target.x = clampNumber(nextX, 0, Math.max(0, editor.canvasWidth - target.w));
    target.y = clampNumber(nextY, 0, Math.max(0, editor.canvasHeight - target.h));
    interaction.changed = true;
    return;
  }

  let nextW = interaction.originW + dx;
  let nextH = interaction.originH + dy;
  if (editor.snapEnabled && !event.altKey) {
    nextW = snapValue(nextW, true);
    nextH = snapValue(nextH, true);
  }
  nextW = clampNumber(nextW, MIN_COMP_W, Math.max(MIN_COMP_W, editor.canvasWidth - target.x));
  nextH = clampNumber(nextH, MIN_COMP_H, Math.max(MIN_COMP_H, editor.canvasHeight - target.y));
  target.w = Math.round(nextW);
  target.h = Math.round(nextH);
  interaction.changed = true;
}

function stopPointerAction() {
  window.removeEventListener("mousemove", onPointerMove);
  window.removeEventListener("mouseup", stopPointerAction);
  if (!interaction.mode) {
    return;
  }
  if (interaction.changed) {
    const target = editor.components.find((item) => item.uid === interaction.targetUid);
    if (target) {
      normalizeComponentBounds(target, editor.snapEnabled);
      if (target.uid === selectedUid.value) {
        syncComponentForm(target);
      }
    }
    commitLayoutChange(true);
  }
  interaction.mode = "";
  interaction.targetUid = "";
  interaction.changed = false;
}

function getWidgetStyle(component) {
  return {
    left: `${component.x}px`,
    top: `${component.y}px`,
    width: `${component.w}px`,
    height: `${component.h}px`,
    zIndex: Number(component.z_index || 1),
  };
}

function datasetNameById(datasetId) {
  if (!datasetId) {
    return "未绑定数据集";
  }
  const matched = datasetList.value.find((item) => Number(item.id) === Number(datasetId));
  if (!matched) {
    return `数据集 #${datasetId}`;
  }
  return matched.name;
}

function normalizeFieldName(fieldName) {
  return String(fieldName || "")
    .trim()
    .toLowerCase();
}

function isIdentifierLikeField(fieldName) {
  const normalized = normalizeFieldName(fieldName);
  if (!normalized) {
    return false;
  }
  return (
    normalized === "id" ||
    normalized.endsWith("_id") ||
    normalized.includes("编号") ||
    normalized.includes("编码") ||
    normalized.includes("code") ||
    normalized.includes("uuid") ||
    normalized.includes("key")
  );
}

function isUrlLikeField(fieldName) {
  const normalized = normalizeFieldName(fieldName);
  if (!normalized) {
    return false;
  }
  return (
    normalized.includes("url") ||
    normalized.includes("link") ||
    normalized.includes("image") ||
    normalized.includes("img") ||
    normalized.includes("图片") ||
    normalized.includes("链接")
  );
}

function metricFieldScore(fieldName) {
  const normalized = normalizeFieldName(fieldName);
  if (!normalized) {
    return -100;
  }
  let score = 0;
  if (isIdentifierLikeField(fieldName)) {
    score -= 100;
  }
  if (normalized.includes("销量") || normalized.includes("销售")) {
    score += 80;
  }
  if (normalized.includes("amount") || normalized.includes("金额") || normalized.includes("总额")) {
    score += 70;
  }
  if (normalized.includes("value") || normalized.includes("数值") || normalized.includes("metric")) {
    score += 60;
  }
  if (normalized.includes("price") || normalized.includes("价格") || normalized.includes("售价")) {
    score += 40;
  }
  if (normalized.includes("count") || normalized.includes("数量") || normalized.includes("总数")) {
    score += 30;
  }
  if (normalized.includes("score") || normalized.includes("评分")) {
    score += 20;
  }
  return score;
}

function dimensionFieldScore(fieldName) {
  const normalized = normalizeFieldName(fieldName);
  if (!normalized) {
    return -100;
  }
  let score = 0;
  if (isUrlLikeField(fieldName)) {
    score -= 100;
  }
  if (isIdentifierLikeField(fieldName)) {
    score -= 60;
  }
  if (normalized.includes("name") || normalized.includes("名称") || normalized.includes("车型")) {
    score += 80;
  }
  if (normalized.includes("category") || normalized.includes("类别") || normalized.includes("类型")) {
    score += 60;
  }
  if (normalized.includes("brand") || normalized.includes("厂商") || normalized.includes("品牌")) {
    score += 40;
  }
  if (normalized.includes("series") || normalized.includes("系列")) {
    score += 30;
  }
  return score;
}

function sortFieldsByScore(fields, scorer) {
  return [...fields].sort((left, right) => {
    const scoreDiff = scorer(right) - scorer(left);
    if (scoreDiff !== 0) {
      return scoreDiff;
    }
    return String(left).localeCompare(String(right), "zh-CN");
  });
}

function pickBestMetricField(meta, excludedFields = []) {
  const excluded = new Set((excludedFields || []).filter(Boolean));
  const numericFields = (meta?.numericFields || []).filter((field) => !excluded.has(field));
  const sorted = sortFieldsByScore(numericFields, metricFieldScore);
  return sorted[0] || numericFields[0] || meta?.fields?.[0] || "";
}

function pickBestDimensionField(meta, excludedFields = []) {
  const excluded = new Set((excludedFields || []).filter(Boolean));
  const dimensionFields = (meta?.dimensionFields || []).filter((field) => !excluded.has(field));
  const sorted = sortFieldsByScore(dimensionFields, dimensionFieldScore);
  return sorted[0] || dimensionFields[0] || meta?.fields?.[0] || "";
}

function toNumberOrNull(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }
  const cleaned = String(value)
    .trim()
    .replace(/,/g, "");
  if (!cleaned) {
    return null;
  }
  const num = Number(cleaned);
  return Number.isFinite(num) ? num : null;
}

function getPreviewCacheKey(datasetId) {
  const id = Number(datasetId || 0);
  return id > 0 ? String(id) : "";
}

async function ensureDatasetPreview(datasetId, force = false) {
  const key = getPreviewCacheKey(datasetId);
  if (!key) {
    return;
  }
  if (!force && datasetPreviewMap[key]) {
    return;
  }
  if (datasetPreviewLoadingMap[key]) {
    return;
  }

  datasetPreviewLoadingMap[key] = true;
  try {
    const result = await fetchDatasetPreview(Number(key), 50);
    const preview = result?.data?.preview || {};
    datasetPreviewMap[key] = {
      columns: Array.isArray(preview.columns) ? preview.columns : [],
      rows: Array.isArray(preview.rows) ? preview.rows : [],
      total_rows: Number(preview.total_rows || 0),
      preview_count: Number(preview.preview_count || 0),
    };
  } catch (error) {
    datasetPreviewMap[key] = {
      columns: [],
      rows: [],
      total_rows: 0,
      preview_count: 0,
      error: error?.message || "数据集预览加载失败",
    };
  } finally {
    delete datasetPreviewLoadingMap[key];
  }
}

function syncBoundDatasetPreviews() {
  const datasetIds = new Set(
    editor.components
      .map((item) => Number(item.dataset_id || 0))
      .filter((item) => Number.isFinite(item) && item > 0)
  );
  for (const id of datasetIds) {
    void ensureDatasetPreview(id);
  }
}

function getDatasetPreviewState(datasetId) {
  const key = getPreviewCacheKey(datasetId);
  if (!key) {
    return null;
  }
  return datasetPreviewMap[key] || null;
}

function getComponentDataNote(component) {
  const datasetId = Number(component?.dataset_id || 0);
  if (!datasetId) {
    return "未绑定数据集（使用组件配置预览）";
  }
  const key = getPreviewCacheKey(datasetId);
  if (datasetPreviewLoadingMap[key]) {
    return "正在加载数据预览...";
  }
  const state = getDatasetPreviewState(datasetId);
  if (!state) {
    return "等待数据预览...";
  }
  if (state.error) {
    return `预览加载失败：${state.error}`;
  }
  if (!state.rows.length) {
    return "数据预览为空（回退到组件配置）";
  }
  return `已加载预览 ${state.preview_count}/${state.total_rows} 行`;
}

function getComponentBindingSummary(component) {
  const binding = getComponentBinding(component);
  const segments = [];
  if (binding.categoryField || binding.category_field) {
    segments.push(`类目:${binding.categoryField || binding.category_field}`);
  }
  if (binding.valueField || binding.value_field || binding.metric) {
    segments.push(`数值:${binding.valueField || binding.value_field || binding.metric}`);
  }
  if (binding.xField || binding.x_field) {
    segments.push(`X:${binding.xField || binding.x_field}`);
  }
  if (binding.yField || binding.y_field) {
    segments.push(`Y:${binding.yField || binding.y_field}`);
  }
  if (binding.seriesField || binding.series_field) {
    segments.push(`系列:${binding.seriesField || binding.series_field}`);
  }
  return segments.join(" | ");
}

function openBindingAssistant() {
  if (!selectedComponent.value) {
    ElMessage.warning("请先选择一个组件");
    return;
  }
  bindingAssistantDialog.visible = true;
}

function applyAllFromAssistant(closeAfterApply = false) {
  if (!selectedComponent.value) {
    return;
  }
  handleSelectedMetaChange();
  handleSelectedGeometryChange();
  const applied = handleSelectedConfigChange(false);
  if (!applied) {
    return;
  }
  ElMessage.success("属性绑定助手配置已应用");
  if (closeAfterApply) {
    bindingAssistantDialog.visible = false;
  }
}

function buildBindingConfigFromForm(baseConfig = {}) {
  const bindingConfig = { ...(baseConfig || {}) };
  const fieldPairs = [
    ["categoryField", componentForm.binding_category_field],
    ["valueField", componentForm.binding_value_field],
    ["xField", componentForm.binding_x_field],
    ["yField", componentForm.binding_y_field],
    ["seriesField", componentForm.binding_series_field],
  ];
  fieldPairs.forEach(([key, value]) => {
    const normalized = String(value || "").trim();
    if (normalized) {
      bindingConfig[key] = normalized;
    } else {
      delete bindingConfig[key];
    }
  });
  return bindingConfig;
}

function openBoundDatasetPreview() {
  const datasetId = Number(componentForm.dataset_id || selectedComponent.value?.dataset_id || 0);
  if (!datasetId) {
    ElMessage.warning("当前组件未绑定数据集");
    return;
  }
  const matchedDataset = datasetList.value.find((item) => Number(item.id) === datasetId);
  dataPreviewDialog.datasetName = matchedDataset?.name || `数据集 #${datasetId}`;
  void ensureDatasetPreview(datasetId, true).then(() => {
    const state = getDatasetPreviewState(datasetId);
    dataPreviewDialog.columns = state?.columns || [];
    dataPreviewDialog.rows = state?.rows || [];
    dataPreviewDialog.totalRows = Number(state?.total_rows || 0);
    dataPreviewDialog.previewCount = Number(state?.preview_count || 0);
    dataPreviewDialog.visible = true;
  });
}

function autoFillBindingFields() {
  const meta = selectedDatasetFieldMeta.value;
  if (!meta.fields.length) {
    ElMessage.warning("请先绑定并加载数据集预览");
    return;
  }
  const categoryField = pickBestDimensionField(meta);
  const valueField = pickBestMetricField(meta, [categoryField]);
  const seriesField = pickBestDimensionField(meta, [categoryField]);
  componentForm.binding_category_field = categoryField;
  componentForm.binding_value_field = valueField;
  componentForm.binding_x_field = categoryField;
  componentForm.binding_y_field = valueField;
  componentForm.binding_series_field = seriesField === categoryField ? "" : seriesField;
  applyBindingFieldsFromForm(true);
}

function applyBindingFieldsFromForm(showMessage = true) {
  const target = selectedComponent.value;
  if (!target) {
    return;
  }
  let baseConfig = {};
  try {
    baseConfig = parseBindingJsonText(componentForm.binding_json_text);
  } catch {
    baseConfig = {};
  }
  target.binding_json = buildBindingConfigFromForm(baseConfig);
  componentForm.binding_json_text = JSON.stringify(target.binding_json, null, 2);
  syncComponentForm(target);
  commitLayoutChange(true);
  if (showMessage) {
    ElMessage.success("字段绑定已应用");
  }
}

function handleSelectedMetaChange() {
  const target = selectedComponent.value;
  if (!target) {
    return;
  }
  const previousDatasetId = Number(target.dataset_id || 0);
  target.title = String(componentForm.title || "").trim().slice(0, 100) || defaultTitleByType(target.type);
  target.dataset_id = componentForm.dataset_id ? Number(componentForm.dataset_id) : null;
  componentForm.title = target.title;
  componentForm.dataset_id = target.dataset_id;
  const nextDatasetId = Number(target.dataset_id || 0);
  if (nextDatasetId > 0 && nextDatasetId !== previousDatasetId) {
    void ensureDatasetPreview(nextDatasetId, true);
  }
  commitLayoutChange(true);
}

function handleSelectedGeometryChange() {
  const target = selectedComponent.value;
  if (!target) {
    return false;
  }
  if (isComponentLocked(target)) {
    ElMessage.warning("该组件已锁定，无法修改位置和尺寸");
    syncComponentForm(target);
    return false;
  }
  target.x = Number(componentForm.x || 0);
  target.y = Number(componentForm.y || 0);
  target.w = Number(componentForm.w || MIN_COMP_W);
  target.h = Number(componentForm.h || MIN_COMP_H);
  target.z_index = Number(componentForm.z_index || 1);
  normalizeComponentBounds(target, editor.snapEnabled);
  target.z_index = clampNumber(target.z_index, 1, 999);
  normalizeZIndices();
  syncComponentForm(target);
  commitLayoutChange(true);
  return true;
}

function parseValueListText(rawText, fallback) {
  const values = String(rawText || "")
    .split(/[,\n]/)
    .map((item) => item.trim())
    .filter((item) => item !== "")
    .map((item) => Number(item))
    .filter((item) => Number.isFinite(item));
  if (!values.length) {
    return fallback;
  }
  return values;
}

function parseLinePointsText(rawText) {
  const points = String(rawText || "")
    .split(/[\n;]+/)
    .map((segment) => segment.trim())
    .filter((segment) => segment)
    .map((segment) => {
      const pair = segment.split(",").map((item) => item.trim());
      if (pair.length < 2) {
        return null;
      }
      const x = Number(pair[0]);
      const y = Number(pair[1]);
      if (!Number.isFinite(x) || !Number.isFinite(y)) {
        return null;
      }
      return { x, y };
    })
    .filter((item) => item);
  if (points.length < 2) {
    return DEFAULT_LINE_POINTS;
  }
  return points;
}

function parsePieSlicesText(rawText) {
  const slices = String(rawText || "")
    .split(/[\n,]+/)
    .map((segment) => segment.trim())
    .filter((segment) => segment)
    .map((segment, index) => {
      const [labelRaw, valueRaw] = segment.split(":");
      const value = Number(valueRaw);
      if (!Number.isFinite(value) || value <= 0) {
        return null;
      }
      const label = String(labelRaw || `分类${index + 1}`).trim() || `分类${index + 1}`;
      return { label, value };
    })
    .filter((item) => item);
  if (!slices.length) {
    return DEFAULT_PIE_SLICES;
  }
  return slices;
}

function parseTableRowsText(rawText) {
  const rows = String(rawText || "")
    .split(/\n+/)
    .map((segment) => segment.trim())
    .filter((segment) => segment);
  if (!rows.length) {
    return DEFAULT_TABLE_ROWS;
  }
  return rows;
}

function parseBindingJsonText(rawText) {
  const text = String(rawText || "").trim();
  if (!text) {
    return {};
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new Error("绑定配置 JSON 格式不正确");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("绑定配置 JSON 必须是对象");
  }
  return parsed;
}

function handleSelectedConfigChange(showMessage = true) {
  const target = selectedComponent.value;
  if (!target) {
    return false;
  }

  let bindingConfig = {};
  try {
    bindingConfig = parseBindingJsonText(componentForm.binding_json_text);
  } catch (error) {
    ElMessage.error(error.message);
    return false;
  }

  const configCandidate = {
    locked: componentForm.locked ? 1 : 0,
    color: String(componentForm.color || "").trim() || DEFAULT_PREVIEW_COLOR,
    bar_values: parseValueListText(componentForm.bar_values_text, DEFAULT_BAR_VALUES),
    line_points: parseLinePointsText(componentForm.line_points_text),
    pie_slices: parsePieSlicesText(componentForm.pie_slices_text),
    table_rows: parseTableRowsText(componentForm.table_rows_text),
    treemap_weights: parseValueListText(componentForm.treemap_weights_text, DEFAULT_TREEMAP_WEIGHTS),
  };

  target.config_json = normalizePreviewConfig(target.type, configCandidate);
  target.binding_json = buildBindingConfigFromForm(bindingConfig);
  componentForm.binding_json_text = JSON.stringify(target.binding_json, null, 2);
  syncComponentForm(target);
  commitLayoutChange(true);
  if (showMessage) {
    ElMessage.success("组件内容配置已应用");
  }
  return true;
}

function handleCanvasConfigChange(pushHistory = true) {
  editor.canvasWidth = clampNumber(editor.canvasWidth, 600, 4096);
  editor.canvasHeight = clampNumber(editor.canvasHeight, 360, 2160);
  editor.zoom = clampNumber(editor.zoom, 30, 180);
  editor.snapSize = clampNumber(editor.snapSize, 4, 200);
  normalizeAllComponents(editor.snapEnabled);
  commitLayoutChange(pushHistory);
}

function alignSelectedToCanvas(mode) {
  const target = selectedComponent.value;
  if (!target) {
    return;
  }
  if (isComponentLocked(target)) {
    ElMessage.warning("组件已锁定，无法执行对齐");
    return;
  }

  if (mode === "left") {
    target.x = 0;
  } else if (mode === "center") {
    target.x = Math.round((editor.canvasWidth - target.w) / 2);
  } else if (mode === "right") {
    target.x = Math.max(0, editor.canvasWidth - target.w);
  } else if (mode === "top") {
    target.y = 0;
  } else if (mode === "middle") {
    target.y = Math.round((editor.canvasHeight - target.h) / 2);
  } else if (mode === "bottom") {
    target.y = Math.max(0, editor.canvasHeight - target.h);
  }

  normalizeComponentBounds(target, editor.snapEnabled);
  syncComponentForm(target);
  commitLayoutChange(true);
}

function nudgeSelectedByKey(dx, dy, useSnapStep = false) {
  const target = selectedComponent.value;
  if (!target) {
    return;
  }
  if (isComponentLocked(target)) {
    return;
  }
  const step = useSnapStep ? clampNumber(editor.snapSize, 4, 200) : 1;
  let nextX = target.x + dx * step;
  let nextY = target.y + dy * step;
  nextX = clampNumber(nextX, 0, Math.max(0, editor.canvasWidth - target.w));
  nextY = clampNumber(nextY, 0, Math.max(0, editor.canvasHeight - target.h));
  target.x = nextX;
  target.y = nextY;
  if (editor.snapEnabled && useSnapStep) {
    normalizeComponentBounds(target, true);
  }
  syncComponentForm(target);
  commitLayoutChange(true);
}

function isEditableTarget(event) {
  const element = event.target;
  if (!element || !(element instanceof HTMLElement)) {
    return false;
  }
  const tag = (element.tagName || "").toLowerCase();
  return tag === "input" || tag === "textarea" || element.isContentEditable;
}

function onKeyDown(event) {
  if (createDialog.visible) {
    return;
  }
  if (isEditableTarget(event)) {
    return;
  }

  const ctrlOrMeta = event.ctrlKey || event.metaKey;
  if (ctrlOrMeta && event.key.toLowerCase() === "s") {
    event.preventDefault();
    void saveCurrentLayout();
    return;
  }

  if (ctrlOrMeta && event.key.toLowerCase() === "z" && !event.shiftKey) {
    event.preventDefault();
    undo();
    return;
  }

  if (
    (ctrlOrMeta && event.shiftKey && event.key.toLowerCase() === "z") ||
    (event.ctrlKey && event.key.toLowerCase() === "y")
  ) {
    event.preventDefault();
    redo();
    return;
  }

  if (ctrlOrMeta && event.key.toLowerCase() === "d") {
    event.preventDefault();
    duplicateSelectedComponent();
    return;
  }

  if ((event.key === "Delete" || event.key === "Backspace") && selectedComponent.value) {
    event.preventDefault();
    removeSelectedComponent(true);
    return;
  }

  if (event.key === "ArrowLeft") {
    event.preventDefault();
    nudgeSelectedByKey(-1, 0, event.shiftKey);
    return;
  }
  if (event.key === "ArrowRight") {
    event.preventDefault();
    nudgeSelectedByKey(1, 0, event.shiftKey);
    return;
  }
  if (event.key === "ArrowUp") {
    event.preventDefault();
    nudgeSelectedByKey(0, -1, event.shiftKey);
    return;
  }
  if (event.key === "ArrowDown") {
    event.preventDefault();
    nudgeSelectedByKey(0, 1, event.shiftKey);
  }
}

function onBeforeUnload(event) {
  if (!editor.isDirty) {
    return;
  }
  event.preventDefault();
  event.returnValue = "";
}

async function confirmDiscardIfDirty(messageText = "当前有未保存修改，继续操作会丢失这些内容，是否继续？") {
  if (!editor.isDirty) {
    return true;
  }
  try {
    await ElMessageBox.confirm(messageText, "未保存修改", {
      type: "warning",
      confirmButtonText: "继续",
      cancelButtonText: "取消",
    });
    return true;
  } catch {
    return false;
  }
}

function applyDashboardDetail(detail) {
  currentDashboard.value = detail;
  currentDashboardId.value = Number(detail.id);
  dashboardSelectId.value = Number(detail.id);

  const layoutJson = detail.layout_json || {};
  editor.canvasWidth = clampNumber(detail.canvas_width, 600, 4096);
  editor.canvasHeight = clampNumber(detail.canvas_height, 360, 2160);
  editor.theme = String(detail.theme || "light");
  editor.zoom = clampNumber(Number(layoutJson.zoom || 70), 30, 180);
  editor.showGrid = Number(layoutJson.show_grid ?? 1) === 1;
  editor.snapEnabled = Number(layoutJson.snap_enabled ?? 1) === 1;
  editor.snapSize = clampNumber(Number(layoutJson.snap_size || 20), 4, 200);

  const sourceComponents = detail.components || [];
  editor.components = sourceComponents.map((item, index) => {
    const type = normalizeType(item.type);
    return {
      uid: newUid(),
      id: item.id || null,
      dataset_id: item.dataset_id || null,
      type,
      title: item.title || defaultTitleByType(type),
      x: Number(item.x || 0),
      y: Number(item.y || 0),
      w: Number(item.w || 320),
      h: Number(item.h || 220),
      z_index: Number(item.z_index || index + 1),
      config_json: item.config_json || {},
      binding_json: item.binding_json || {},
    };
  });

  normalizeAllComponents(false);
  normalizeZIndices();
  selectedUid.value = "";
  resetComponentForm();
  syncBoundDatasetPreviews();
  commitSavedSnapshot();
  resetHistory();
}

function mixHexWithWhite(hexColor, ratio = 0.25) {
  const hex = String(hexColor || "").trim().replace("#", "");
  if (!/^[0-9a-fA-F]{6}$/.test(hex)) {
    return hexColor;
  }
  const base = parseInt(hex, 16);
  const r = (base >> 16) & 0xff;
  const g = (base >> 8) & 0xff;
  const b = base & 0xff;
  const nextR = Math.round(r + (255 - r) * ratio);
  const nextG = Math.round(g + (255 - g) * ratio);
  const nextB = Math.round(b + (255 - b) * ratio);
  return `rgb(${nextR}, ${nextG}, ${nextB})`;
}

function getComponentBinding(component) {
  const binding = component?.binding_json;
  if (!binding || typeof binding !== "object" || Array.isArray(binding)) {
    return {};
  }
  return binding;
}

function resolveBindingField(binding, rows, columns, candidates) {
  const byName = new Set((columns || []).map((field) => normalizeFieldName(field)));
  const firstRow = rows[0] || {};
  for (const key of candidates) {
    const direct = binding[key];
    if (typeof direct === "string" && direct.trim()) {
      return direct.trim();
    }
  }
  const normalizedCandidates = new Set(candidates.map((item) => normalizeFieldName(item)));
  for (const [key, value] of Object.entries(binding)) {
    if (!normalizedCandidates.has(normalizeFieldName(key))) {
      continue;
    }
    if (typeof value === "string" && value.trim()) {
      return value.trim();
    }
  }
  for (const field of columns || []) {
    if (field in firstRow || byName.has(normalizeFieldName(field))) {
      continue;
    }
  }
  return "";
}

function detectDatasetFieldMeta(rows, columns) {
  const fields = Array.isArray(columns) && columns.length ? columns : Object.keys(rows[0] || {});
  const numericFields = [];
  const dimensionFields = [];

  for (const field of fields) {
    const values = rows.map((row) => row?.[field]).filter((value) => value !== null && value !== undefined && value !== "");
    if (!values.length) {
      continue;
    }
    let numericCount = 0;
    for (const value of values) {
      if (toNumberOrNull(value) !== null) {
        numericCount += 1;
      }
    }
    const ratio = numericCount / values.length;
    if (ratio >= 0.6) {
      numericFields.push(field);
    } else {
      dimensionFields.push(field);
    }
  }

  if (!dimensionFields.length && fields.length) {
    const fallback = fields.find((field) => !numericFields.includes(field));
    if (fallback) {
      dimensionFields.push(fallback);
    }
  }

  return {
    fields,
    numericFields,
    dimensionFields,
  };
}

function aggregateRowsByField(rows, categoryField, valueField) {
  const normalizedValueField = String(valueField || "").trim();
  const resolveCategory = (row, index) =>
    String((categoryField ? row?.[categoryField] : null) ?? `第${index + 1}项`).trim() || `第${index + 1}项`;
  const bucket = new Map();
  let hasNumericValue = false;

  rows.forEach((row, index) => {
    const category = resolveCategory(row, index);
    if (!normalizedValueField) {
      bucket.set(category, (bucket.get(category) || 0) + 1);
      return;
    }

    const numeric = toNumberOrNull(row?.[normalizedValueField]);
    if (numeric === null) {
      return;
    }
    hasNumericValue = true;
    bucket.set(category, (bucket.get(category) || 0) + numeric);
  });

  // 如果绑定了值字段但数据里没有可用数值，回退为按类目计数，保证绑定后有可见反馈。
  if (normalizedValueField && !hasNumericValue) {
    rows.forEach((row, index) => {
      const category = resolveCategory(row, index);
      bucket.set(category, (bucket.get(category) || 0) + 1);
    });
  }

  return [...bucket.entries()]
    .map(([name, value]) => ({ name, value: Number(value || 0) }))
    .filter((item) => Number.isFinite(item.value) && item.value > 0)
    .sort((a, b) => b.value - a.value);
}

function formatMetric(value) {
  const num = Number(value || 0);
  if (!Number.isFinite(num)) {
    return "0";
  }
  return num.toLocaleString("zh-CN", { maximumFractionDigits: 2 });
}

function buildDatasetDrivenPreview(component) {
  const datasetId = Number(component?.dataset_id || 0);
  if (!datasetId) {
    return null;
  }
  const previewState = getDatasetPreviewState(datasetId);
  const rows = previewState?.rows || [];
  if (!rows.length) {
    return null;
  }
  const columns = previewState?.columns || [];
  const binding = getComponentBinding(component);
  const fieldMeta = detectDatasetFieldMeta(rows, columns);
  const fields = fieldMeta.fields;
  const numericFields = fieldMeta.numericFields;
  const dimensionFields = fieldMeta.dimensionFields;
  const resolvedValueField = resolveBindingField(binding, rows, fields, [
    "valueField",
    "value_field",
    "metric",
    "yField",
    "y_field",
  ]);
  const valueField =
    (resolvedValueField && !isIdentifierLikeField(resolvedValueField) && !isUrlLikeField(resolvedValueField)
      ? resolvedValueField
      : "") ||
    pickBestMetricField(fieldMeta) ||
    "";
  const resolvedCategoryField = resolveBindingField(binding, rows, fields, [
    "categoryField",
    "category_field",
    "nameField",
    "name_field",
    "xField",
    "x_field",
  ]);
  const categoryField =
    (resolvedCategoryField && !isUrlLikeField(resolvedCategoryField) ? resolvedCategoryField : "") ||
    pickBestDimensionField(fieldMeta) ||
    fields[0] ||
    "";
  const aggregated = aggregateRowsByField(rows, categoryField, valueField);
  const fallbackColor = getPreviewConfig(component).color;

  if (component.type === "bar") {
    if (!aggregated.length) {
      return null;
    }
    const top = aggregated.slice(0, 5);
    const values = top.map((item) => item.value);
    const maxValue = Math.max(...values, 1);
    const minValue = Math.min(...values, 0);
    return {
      color: fallbackColor,
      bar_values: top.map((item) => {
        if (maxValue <= minValue) {
          return 72;
        }
        const ratio = (item.value - minValue) / Math.max(maxValue - minValue, 1e-9);
        return clampNumber(24 + ratio * 68, 24, 96);
      }),
      bar_labels: top.map((item) => item.name),
      bar_metric_values: top.map((item) => item.value),
    };
  }

  if (component.type === "line") {
    const xField =
      resolveBindingField(binding, rows, fields, ["xField", "x_field", "categoryField", "category_field", "nameField", "name_field"]) ||
      categoryField;
    const yField =
      resolveBindingField(binding, rows, fields, ["yField", "y_field", "valueField", "value_field", "metric"]) ||
      valueField;
    const series = rows
      .slice(0, 10)
      .map((row, index) => {
        const yValue = toNumberOrNull(row?.[yField]);
        if (yValue === null) {
          return null;
        }
        const rawLabel = xField ? row?.[xField] : null;
        const label = String(rawLabel ?? `P${index + 1}`).trim() || `P${index + 1}`;
        return { index, y: yValue, label };
      })
      .filter((item) => item);
    if (series.length < 2) {
      return null;
    }
    const minY = Math.min(...series.map((item) => item.y));
    const maxY = Math.max(...series.map((item) => item.y));
    const pointCount = Math.max(series.length - 1, 1);
    const line_points = series.map((item, index) => {
      const x = (index / pointCount) * 100;
      const y =
        maxY === minY
          ? 52
          : 88 - ((item.y - minY) / Math.max(maxY - minY, 1e-9)) * 72;
      return { x: clampNumber(x, 0, 100), y: clampNumber(y, 6, 94) };
    });
    return {
      color: fallbackColor,
      line_points,
      line_labels: series.map((item) => item.label.slice(0, 10)),
    };
  }

  if (component.type === "pie") {
    if (!aggregated.length) {
      return null;
    }
    return {
      color: fallbackColor,
      pie_slices: aggregated.slice(0, 6).map((item) => ({
        label: item.name,
        value: Math.max(1, Math.round(item.value)),
      })),
    };
  }

  if (component.type === "table") {
    const viewRows = rows.slice(0, 6);
    const table_rows = viewRows.map((row, index) => {
      const left = categoryField ? String(row?.[categoryField] ?? `第${index + 1}项`).trim() : `第${index + 1}项`;
      const numeric = valueField ? toNumberOrNull(row?.[valueField]) : null;
      if (numeric === null) {
        return left || `第${index + 1}项`;
      }
      return `${left}: ${formatMetric(numeric)}`;
    });
    return {
      color: fallbackColor,
      table_rows,
    };
  }

  if (component.type === "treemap") {
    if (!aggregated.length) {
      return null;
    }
    const top = aggregated.slice(0, 5);
    const sum = top.reduce((acc, item) => acc + item.value, 0) || 1;
    const weights = top.map((item) => Math.max(2, Math.round((item.value / sum) * 100)));
    return {
      color: fallbackColor,
      treemap_weights: weights,
      treemap_labels: top.map((item) => item.name),
    };
  }

  return null;
}

function getResolvedPreviewConfig(component) {
  const fallback = getPreviewConfig(component);
  const datasetDriven = buildDatasetDrivenPreview(component);
  if (!datasetDriven) {
    return fallback;
  }
  const normalized = normalizePreviewConfig(component.type, {
    ...fallback,
    ...datasetDriven,
    color: fallback.color,
  });
  if (Array.isArray(datasetDriven.bar_labels)) {
    normalized.bar_labels = datasetDriven.bar_labels;
  }
  if (Array.isArray(datasetDriven.bar_metric_values)) {
    normalized.bar_metric_values = datasetDriven.bar_metric_values;
  }
  if (Array.isArray(datasetDriven.line_labels)) {
    normalized.line_labels = datasetDriven.line_labels;
  }
  if (Array.isArray(datasetDriven.treemap_labels)) {
    normalized.treemap_labels = datasetDriven.treemap_labels;
  }
  return normalized;
}

function getBarPreviewValues(component) {
  return getResolvedPreviewConfig(component).bar_values;
}

function getBarPreviewLabels(component) {
  const config = getResolvedPreviewConfig(component);
  return Array.isArray(config.bar_labels) ? config.bar_labels : [];
}

function getBarPreviewMetricValues(component) {
  const config = getResolvedPreviewConfig(component);
  return Array.isArray(config.bar_metric_values) ? config.bar_metric_values : [];
}

function getBarPreviewLabelAt(component, index) {
  const labels = getBarPreviewLabels(component);
  const label = labels[index] || `分类${index + 1}`;
  return String(label).slice(0, 8);
}

function getBarPreviewMetricAt(component, index) {
  const values = getBarPreviewMetricValues(component);
  const value = values[index];
  if (value === undefined) {
    return "";
  }
  return formatMetric(value);
}

function getBarStyle(component, heightPercent) {
  const color = getResolvedPreviewConfig(component).color;
  return {
    height: `${clampNumber(Number(heightPercent || 0), 8, 98)}%`,
    background: `linear-gradient(180deg, ${mixHexWithWhite(color, 0.28)} 0%, ${color} 100%)`,
  };
}

function getLinePreviewPoints(component) {
  const w = Math.max(80, Number(component.w || 200) - 18);
  const h = Math.max(60, Number(component.h || 150) - 28);
  const points = getResolvedPreviewConfig(component).line_points;
  return points
    .map((point) => {
      const x = Math.round((clampNumber(point.x, 0, 100) / 100) * w);
      const y = Math.round((clampNumber(point.y, 0, 100) / 100) * h);
      return `${x},${y}`;
    })
    .join(" ");
}

function getLinePreviewNodes(component) {
  const w = Math.max(80, Number(component.w || 200) - 18);
  const h = Math.max(60, Number(component.h || 150) - 28);
  const config = getResolvedPreviewConfig(component);
  const points = Array.isArray(config.line_points) ? config.line_points : [];
  const labels = Array.isArray(config.line_labels) ? config.line_labels : [];
  const lastIndex = Math.max(points.length - 1, 0);
  return points.map((point, index) => {
    const x = Math.round((clampNumber(point.x, 0, 100) / 100) * w);
    const y = Math.round((clampNumber(point.y, 0, 100) / 100) * h);
    const rawLabel = labels[index] || `P${index + 1}`;
    const showLabel = points.length <= 6 || index % 2 === 0 || index === lastIndex;
    return {
      x,
      y,
      label: String(rawLabel).slice(0, 8),
      showLabel,
    };
  });
}

function getLineStrokeColor(component) {
  return getResolvedPreviewConfig(component).color;
}

function getPieGradient(component) {
  const config = getResolvedPreviewConfig(component);
  const total = config.pie_slices.reduce((sum, item) => sum + Number(item.value || 0), 0) || 1;
  const slices = [];
  let current = 0;
  config.pie_slices.forEach((item, index) => {
    const percent = (Number(item.value || 0) / total) * 100;
    const start = current;
    const end = clampNumber(current + percent, 0, 100);
    current = end;
    const color = index === 0 ? config.color : mixHexWithWhite(config.color, 0.2 * (index + 1));
    slices.push(`${color} ${start.toFixed(2)}% ${end.toFixed(2)}%`);
  });
  return `conic-gradient(${slices.join(", ")})`;
}

function getPieSliceLabels(component) {
  const config = getResolvedPreviewConfig(component);
  const slices = Array.isArray(config.pie_slices) ? config.pie_slices : [];
  const total = slices.reduce((sum, item) => sum + Number(item.value || 0), 0) || 1;
  let current = 0;
  const radius = 39;
  return slices.slice(0, 6).map((slice, index) => {
    const percent = (Number(slice.value || 0) / total) * 100;
    const mid = current + percent / 2;
    current += percent;
    const angle = (mid / 100) * Math.PI * 2 - Math.PI / 2;
    const x = 50 + Math.cos(angle) * radius;
    const y = 50 + Math.sin(angle) * radius;
    return {
      id: `${index}-${slice.label}`,
      label: String(slice.label || `分类${index + 1}`).slice(0, 7),
      x: clampNumber(x, 6, 94),
      y: clampNumber(y, 8, 92),
    };
  });
}

function getTablePreviewRows(component) {
  const config = getResolvedPreviewConfig(component);
  return config.table_rows.map((label, index) => ({
    label,
    width: clampNumber(92 - index * 10, 46, 96),
  }));
}

function getTableRowStyle(component, row) {
  const color = getResolvedPreviewConfig(component).color;
  return {
    width: `${row.width}%`,
    background: `linear-gradient(90deg, ${mixHexWithWhite(color, 0.52)} 0%, ${mixHexWithWhite(color, 0.26)} 100%)`,
  };
}

function getTreemapCellStyle(component, index) {
  const config = getResolvedPreviewConfig(component);
  const weight = config.treemap_weights[index] ?? DEFAULT_TREEMAP_WEIGHTS[index] ?? 10;
  const ratio = clampNumber(Number(weight) / 100, 0.12, 0.9);
  const color = index === 0 ? config.color : mixHexWithWhite(config.color, 0.16 * index);
  return {
    background: color,
    opacity: ratio,
  };
}

function getTreemapPreviewLabels(component) {
  const config = getResolvedPreviewConfig(component);
  return Array.isArray(config.treemap_labels) ? config.treemap_labels : [];
}

function getTreemapCellLabel(component, index) {
  const labels = getTreemapPreviewLabels(component);
  const label = labels[index] || `分类${index + 1}`;
  return String(label).slice(0, 8);
}

async function loadDashboardDetail(dashboardId, options = {}) {
  const { skipDirtyCheck = false, quiet = false } = options;
  const targetId = Number(dashboardId || 0);
  if (!targetId) {
    return false;
  }

  if (!skipDirtyCheck && targetId !== Number(currentDashboardId.value || 0)) {
    const confirmed = await confirmDiscardIfDirty("切换大屏会丢失当前未保存修改，是否继续？");
    if (!confirmed) {
      dashboardSelectId.value = currentDashboardId.value;
      return false;
    }
  }

  loading.detail = true;
  try {
    const result = await fetchDashboardDetail(targetId);
    const detail = result?.data || null;
    if (!detail) {
      throw new Error("未获取到大屏详情");
    }
    applyDashboardDetail(detail);
    if (!quiet) {
      ElMessage.success(`已加载大屏：${detail.name}`);
    }
    return true;
  } catch (error) {
    if (!quiet) {
      ElMessage.error(error.message);
    }
    dashboardSelectId.value = currentDashboardId.value;
    return false;
  } finally {
    loading.detail = false;
  }
}

async function loadDashboardList(preferredId = null, autoLoad = true) {
  loading.dashboards = true;
  try {
    const result = await fetchDashboards(1, 100);
    dashboardList.value = result?.data || [];
    if (!dashboardList.value.length) {
      dashboardSelectId.value = null;
      currentDashboardId.value = null;
      currentDashboard.value = null;
      createEmptyEditorState();
      return;
    }
    const availableIds = new Set(dashboardList.value.map((item) => Number(item.id)));
    const targetId =
      Number(preferredId && availableIds.has(Number(preferredId)) ? preferredId : 0) ||
      Number(currentDashboardId.value && availableIds.has(Number(currentDashboardId.value)) ? currentDashboardId.value : 0) ||
      Number(dashboardList.value[0].id);
    dashboardSelectId.value = targetId;
    if (autoLoad) {
      await loadDashboardDetail(targetId, { skipDirtyCheck: true, quiet: true });
    }
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loading.dashboards = false;
  }
}

async function loadDatasets() {
  loading.datasets = true;
  try {
    const pageSize = 100;
    let page = 1;
    let totalPages = 1;
    const merged = [];

    while (page <= totalPages) {
      const result = await fetchDatasets(page, pageSize);
      merged.push(...(result?.data || []));
      totalPages = Math.max(1, Number(result?.pagination?.total_pages || 1));
      page += 1;
    }

    datasetList.value = merged;
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loading.datasets = false;
  }
}

async function handleDashboardSelectChange(value) {
  const targetId = Number(value || 0);
  if (!targetId || targetId === Number(currentDashboardId.value || 0)) {
    return;
  }
  await loadDashboardDetail(targetId);
}

function openCreateDialog() {
  createForm.name = "";
  createForm.description = "";
  createForm.canvas_width = 1920;
  createForm.canvas_height = 1080;
  createForm.theme = "light";
  createDialog.visible = true;
}

async function submitCreateDashboard() {
  const name = String(createForm.name || "").trim();
  if (!name) {
    ElMessage.warning("请输入大屏名称");
    return;
  }
  createDialog.submitting = true;
  try {
    const payload = {
      name,
      description: String(createForm.description || "").trim() || null,
      canvas_width: clampNumber(createForm.canvas_width, 600, 4096),
      canvas_height: clampNumber(createForm.canvas_height, 360, 2160),
      theme: createForm.theme || "light",
    };
    const result = await createDashboard(payload);
    const created = result?.data || null;
    createDialog.visible = false;
    ElMessage.success("大屏创建成功");
    await loadDashboardList(created?.id || null, false);
    if (created?.id) {
      await loadDashboardDetail(created.id, { skipDirtyCheck: true, quiet: true });
    } else if (dashboardSelectId.value) {
      await loadDashboardDetail(dashboardSelectId.value, { skipDirtyCheck: true, quiet: true });
    }
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    createDialog.submitting = false;
  }
}

async function removeCurrentDashboard() {
  if (!currentDashboardId.value || !currentDashboard.value) {
    ElMessage.warning("当前没有可删除的大屏");
    return;
  }
  try {
    await ElMessageBox.confirm(
      `确认删除大屏「${currentDashboard.value.name}」吗？删除后不可恢复。`,
      "删除确认",
      {
        type: "warning",
        confirmButtonText: "确认删除",
        cancelButtonText: "取消",
      }
    );
  } catch {
    return;
  }

  try {
    await deleteDashboard(currentDashboardId.value);
    ElMessage.success("大屏已删除");
    await loadDashboardList(null, false);
    if (dashboardList.value.length) {
      await loadDashboardDetail(dashboardList.value[0].id, { skipDirtyCheck: true, quiet: true });
    }
  } catch (error) {
    ElMessage.error(error.message);
  }
}

async function handlePublishChange(nextValue) {
  if (!currentDashboardId.value) {
    return;
  }
  try {
    await publishDashboard(currentDashboardId.value, Boolean(nextValue));
    if (currentDashboard.value) {
      currentDashboard.value.is_published = nextValue ? 1 : 0;
    }
    ElMessage.success(nextValue ? "已发布" : "已取消发布");
    await loadDashboardList(currentDashboardId.value, false);
  } catch (error) {
    ElMessage.error(error.message);
  }
}

async function saveCurrentLayout() {
  if (!currentDashboardId.value) {
    ElMessage.warning("请先创建或选择大屏");
    return;
  }

  loading.saving = true;
  try {
    normalizeAllComponents(editor.snapEnabled);
    normalizeZIndices();

    await updateDashboard(currentDashboardId.value, {
      canvas_width: clampNumber(editor.canvasWidth, 600, 4096),
      canvas_height: clampNumber(editor.canvasHeight, 360, 2160),
      theme: editor.theme,
    });

    const components = [...editor.components]
      .sort((a, b) => Number(a.z_index || 0) - Number(b.z_index || 0))
      .map((item, index) => toPersistComponent(item, index));

    await saveDashboardLayout(currentDashboardId.value, {
      layout_json: {
        zoom: editor.zoom,
        show_grid: editor.showGrid ? 1 : 0,
        snap_enabled: editor.snapEnabled ? 1 : 0,
        snap_size: editor.snapSize,
      },
      components,
    });

    await loadDashboardDetail(currentDashboardId.value, {
      skipDirtyCheck: true,
      quiet: true,
    });
    await loadDashboardList(currentDashboardId.value, false);
    ElMessage.success("布局保存成功");
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loading.saving = false;
  }
}

function resetZoom() {
  editor.zoom = 100;
  handleCanvasConfigChange(true);
}

function undo() {
  if (!canUndo.value) {
    return;
  }
  historyState.index -= 1;
  restoreHistorySnapshot(historyState.stack[historyState.index]);
}

function redo() {
  if (!canRedo.value) {
    return;
  }
  historyState.index += 1;
  restoreHistorySnapshot(historyState.stack[historyState.index]);
}

watch(
  () => selectedUid.value,
  () => {
    syncComponentForm(selectedComponent.value);
  },
  { immediate: true }
);

watch(
  () => componentForm.dataset_id,
  (nextId, previousId) => {
    const next = Number(nextId || 0);
    const prev = Number(previousId || 0);
    if (next > 0 && next !== prev) {
      void ensureDatasetPreview(next);
    }
  }
);

onBeforeRouteLeave(async () => {
  const ok = await confirmDiscardIfDirty("离开当前页面会丢失未保存修改，是否继续？");
  if (!ok) {
    return false;
  }
  return true;
});

onMounted(async () => {
  window.addEventListener("keydown", onKeyDown);
  window.addEventListener("beforeunload", onBeforeUnload);
  await Promise.all([loadDatasets(), loadDashboardList(null, true)]);
  syncBoundDatasetPreviews();
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onKeyDown);
  window.removeEventListener("beforeunload", onBeforeUnload);
  stopPointerAction();
});
</script>
<template>
  <div class="page-wrap feature-page">
    <el-card shadow="never" class="feature-hero-card">
      <div class="feature-hero-head">
        <div>
          <h2>大屏编辑器</h2>
          <p>
            在当前版本基础上，新增了网格吸附、缩放、撤销重做、复制组件、快捷键和未保存拦截，适合从演示版走向可持续编辑版本。
          </p>
        </div>
      </div>
    </el-card>

    <div class="dashboard-editor">
      <el-card shadow="never" class="feature-section-card editor-side section-fill">
        <template #header>
          <div class="section-head">
            <el-icon class="section-icon"><CollectionTag /></el-icon>
            <span>大屏与组件</span>
          </div>
        </template>

        <div class="editor-side-block">
          <div class="toolbar-label">大屏选择</div>
          <el-select
            v-model="dashboardSelectId"
            class="dashboard-select"
            filterable
            clearable
            placeholder="请选择大屏"
            :loading="loading.dashboards"
            @change="handleDashboardSelectChange"
          >
            <el-option
              v-for="item in dashboardList"
              :key="item.id"
              :label="`${item.name} (ID:${item.id})`"
              :value="item.id"
            />
          </el-select>

          <div class="editor-dashboard-actions">
            <el-button type="primary" plain @click="openCreateDialog">新建</el-button>
            <el-button @click="loadDashboardList(currentDashboardId, false)">刷新</el-button>
            <el-button type="danger" plain @click="removeCurrentDashboard">删除</el-button>
          </div>

          <div class="editor-publish-line">
            <span class="toolbar-label">发布状态</span>
            <div class="editor-publish-controls">
              <el-tag size="small" :type="publishStatusTagType">{{ publishStatusText }}</el-tag>
              <el-switch
                :model-value="publishStatus"
                :disabled="!currentDashboardId"
                @change="handlePublishChange"
              />
            </div>
          </div>
        </div>

        <el-divider />

        <div class="editor-side-block">
          <div class="toolbar-label">组件库</div>
          <div class="library-list">
            <div v-for="item in COMPONENT_LIBRARY" :key="item.type" class="library-item">
              <div>
                <strong>{{ item.name }}</strong>
                <p>{{ item.desc }}</p>
              </div>
              <el-button type="primary" text @click="addComponent(item.type)">添加</el-button>
            </div>
          </div>
        </div>

        <el-alert
          class="editor-alert"
          type="info"
          :closable="false"
          title="快捷键：Ctrl+S 保存，Ctrl+Z 撤销，Ctrl+Shift+Z/ Ctrl+Y 重做，Ctrl+D 复制，Delete 删除，方向键微调（Shift 为大步长）"
        />
      </el-card>

      <el-card shadow="never" class="feature-section-card editor-canvas-wrap">
        <template #header>
          <div class="section-head">
            <el-icon class="section-icon"><DataAnalysis /></el-icon>
            <span>画布编辑区</span>
          </div>
        </template>

        <div class="editor-toolbar">
          <div class="toolbar-main">
            <div class="toolbar-group">
              <el-button size="small" :disabled="!canUndo" @click="undo">撤销</el-button>
              <el-button size="small" :disabled="!canRedo" @click="redo">重做</el-button>
              <el-button size="small" :disabled="!selectedComponent" @click="duplicateSelectedComponent">
                复制
              </el-button>
              <el-button size="small" :disabled="!selectedComponent" @click="removeSelectedComponent">
                删除
              </el-button>
            </div>

            <div class="toolbar-group" v-if="selectedComponent">
              <span class="toolbar-label">对齐</span>
              <el-button size="small" @click="alignSelectedToCanvas('left')">左</el-button>
              <el-button size="small" @click="alignSelectedToCanvas('center')">中</el-button>
              <el-button size="small" @click="alignSelectedToCanvas('right')">右</el-button>
              <el-button size="small" @click="alignSelectedToCanvas('top')">上</el-button>
              <el-button size="small" @click="alignSelectedToCanvas('middle')">中线</el-button>
              <el-button size="small" @click="alignSelectedToCanvas('bottom')">下</el-button>
            </div>

            <div class="toolbar-group">
              <span class="toolbar-label">网格</span>
              <el-switch v-model="editor.showGrid" @change="handleCanvasConfigChange(false)" />
              <span class="toolbar-label">吸附</span>
              <el-switch v-model="editor.snapEnabled" @change="handleCanvasConfigChange(true)" />
              <span class="toolbar-label">间距</span>
              <el-input-number
                v-model="editor.snapSize"
                :min="4"
                :max="200"
                :step="2"
                size="small"
                @change="handleCanvasConfigChange(true)"
              />
            </div>

            <div class="toolbar-group toolbar-zoom">
              <span class="toolbar-label">缩放</span>
              <el-slider
                v-model="editor.zoom"
                :min="30"
                :max="180"
                :step="5"
                show-input
                @change="handleCanvasConfigChange(false)"
              />
              <el-button size="small" @click="resetZoom">100%</el-button>
            </div>
          </div>

          <div class="toolbar-group">
            <el-tag :type="editor.isDirty ? 'warning' : 'success'">
              {{ editor.isDirty ? "未保存" : "已保存" }}
            </el-tag>
            <el-button type="primary" :loading="loading.saving" @click="saveCurrentLayout">保存布局</el-button>
          </div>
        </div>

        <div v-if="loading.detail" class="canvas-loading">正在加载大屏详情...</div>

        <div v-else class="editor-canvas-scroll">
          <div class="editor-canvas-stage" :style="canvasStageStyle">
            <div class="editor-canvas" :class="canvasThemeClass" :style="canvasStyle" @mousedown.self="clearSelection">
              <div v-if="editor.showGrid" class="editor-grid-layer" :style="gridStyle"></div>

              <div
                v-for="component in sortedComponents"
                :key="component.uid"
                class="editor-widget"
                :class="{ active: component.uid === selectedUid, locked: isComponentLocked(component) }"
                :style="getWidgetStyle(component)"
                @mousedown.stop="selectComponent(component.uid)"
              >
                <div class="editor-widget-header" @mousedown.stop="startMove(component, $event)">
                  <span>{{ component.title || defaultTitleByType(component.type) }}</span>
                  <small>
                    {{ getTypeLabel(component.type) }}
                    <template v-if="isComponentLocked(component)"> · 锁定</template>
                  </small>
                </div>

                <div class="editor-widget-body">
                  <div class="widget-meta">{{ datasetNameById(component.dataset_id) }}</div>
                  <div class="widget-meta-sub">{{ getComponentDataNote(component) }}</div>
                  <div v-if="getComponentBindingSummary(component)" class="widget-binding-summary">
                    {{ getComponentBindingSummary(component) }}
                  </div>

                  <div v-if="component.type === 'bar'" class="widget-preview widget-preview-bar">
                    <div
                      v-for="(height, index) in getBarPreviewValues(component)"
                      :key="`bar-${component.uid}-${index}`"
                      class="bar-item"
                    >
                      <span v-if="getBarPreviewMetricAt(component, index)" class="bar-value">
                        {{ getBarPreviewMetricAt(component, index) }}
                      </span>
                      <div class="bar" :style="getBarStyle(component, height)"></div>
                      <span class="bar-label">
                        {{ getBarPreviewLabelAt(component, index) }}
                      </span>
                    </div>
                  </div>

                  <div v-else-if="component.type === 'line'" class="widget-preview widget-preview-line">
                    <svg :viewBox="`0 0 ${Math.max(80, component.w - 18)} ${Math.max(60, component.h - 28)}`" preserveAspectRatio="none">
                      <polyline :points="getLinePreviewPoints(component)" :stroke="getLineStrokeColor(component)" />
                      <g v-for="(node, index) in getLinePreviewNodes(component)" :key="`line-node-${component.uid}-${index}`">
                        <circle class="line-node-dot" :cx="node.x" :cy="node.y" r="2.8" />
                        <text
                          v-if="node.showLabel"
                          class="line-node-label"
                          :x="node.x"
                          :y="Math.max(node.y - 5, 8)"
                          text-anchor="middle"
                        >
                          {{ node.label }}
                        </text>
                      </g>
                    </svg>
                  </div>

                  <div v-else-if="component.type === 'pie'" class="widget-preview widget-preview-pie">
                    <div class="pie" :style="{ background: getPieGradient(component) }"></div>
                    <span
                      v-for="slice in getPieSliceLabels(component)"
                      :key="`pie-label-${component.uid}-${slice.id}`"
                      class="pie-label"
                      :style="{ left: `${slice.x}%`, top: `${slice.y}%` }"
                    >
                      {{ slice.label }}
                    </span>
                  </div>

                  <div v-else-if="component.type === 'table'" class="widget-preview widget-preview-table">
                    <div
                      v-for="(row, index) in getTablePreviewRows(component)"
                      :key="`table-${component.uid}-${index}`"
                      class="row"
                      :style="getTableRowStyle(component, row)"
                    >
                      <span>{{ row.label }}</span>
                    </div>
                  </div>

                  <div v-else class="widget-preview widget-preview-treemap">
                    <span
                      v-for="(_, index) in 5"
                      :key="`treemap-${component.uid}-${index}`"
                      class="cell"
                      :class="`c${index + 1}`"
                      :style="getTreemapCellStyle(component, index)"
                    >
                      <span class="cell-label">
                        {{ getTreemapCellLabel(component, index) }}
                      </span>
                    </span>
                  </div>
                </div>

                <span
                  v-if="!isComponentLocked(component)"
                  class="editor-resize-handle"
                  @mousedown.stop="startResize(component, $event)"
                ></span>
              </div>
            </div>
          </div>
        </div>
      </el-card>
      <el-card shadow="never" class="feature-section-card editor-side section-fill">
        <template #header>
          <div class="panel-header-row">
            <div class="section-head">
              <el-icon class="section-icon"><SetUp /></el-icon>
              <span>属性面板</span>
            </div>
            <el-button
              size="small"
              type="primary"
              plain
              :disabled="!selectedComponent"
              @click="openBindingAssistant"
            >
              属性绑定助手
            </el-button>
          </div>
        </template>

        <div class="editor-side-block">
          <div class="toolbar-label">画布配置</div>
          <el-form label-position="top">
            <el-row :gutter="8">
              <el-col :span="12">
                <el-form-item label="宽度">
                  <el-input-number
                    v-model="editor.canvasWidth"
                    :min="600"
                    :max="4096"
                    @change="handleCanvasConfigChange(true)"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="高度">
                  <el-input-number
                    v-model="editor.canvasHeight"
                    :min="360"
                    :max="2160"
                    @change="handleCanvasConfigChange(true)"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="主题">
              <el-select v-model="editor.theme" @change="handleCanvasConfigChange(true)">
                <el-option label="light" value="light" />
                <el-option label="dark" value="dark" />
                <el-option label="tech-blue" value="tech-blue" />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <el-divider />

        <div class="editor-side-block">
          <div class="toolbar-label">组件属性</div>
          <div v-if="selectedComponent">
            <div class="component-quick-summary">
              <div class="summary-row">
                <span>标题</span>
                <strong>{{ componentForm.title || defaultTitleByType(selectedComponent.type) }}</strong>
              </div>
              <div class="summary-row">
                <span>类型</span>
                <strong>{{ getTypeLabel(selectedComponent.type) }}</strong>
              </div>
              <div class="summary-row">
                <span>数据集</span>
                <strong>{{ datasetNameById(componentForm.dataset_id) }}</strong>
              </div>
              <div class="summary-row">
                <span>位置</span>
                <strong>X: {{ componentForm.x }} / Y: {{ componentForm.y }}</strong>
              </div>
              <div class="summary-row">
                <span>尺寸</span>
                <strong>{{ componentForm.w }} × {{ componentForm.h }}</strong>
              </div>
              <div class="summary-row">
                <span>层级</span>
                <strong>{{ componentForm.z_index }}</strong>
              </div>
            </div>

            <div class="compact-helper-panel">
              <p class="compact-helper-title">绑定与内容配置</p>
              <p class="compact-helper-desc">
                {{
                  getComponentBindingSummary(selectedComponent) ||
                  "当前未配置字段映射，可在属性绑定助手中进行自动映射和手动调整。"
                }}
              </p>
              <div class="compact-helper-actions">
                <el-button size="small" @click="openBindingAssistant">打开属性绑定助手</el-button>
                <el-button size="small" @click="openBoundDatasetPreview">查看数据预览</el-button>
              </div>
            </div>

            <div class="compact-helper-actions">
              <el-button size="small" @click="moveSelectedZ(false)">下移一层</el-button>
              <el-button size="small" @click="moveSelectedZ(true)">上移一层</el-button>
            </div>
          </div>
          <div v-else class="empty-note">请选择画布中的组件以编辑属性。</div>
        </div>
      </el-card>
    </div>

    <el-dialog v-model="createDialog.visible" title="新建大屏" width="540px">
      <el-form label-position="top">
        <el-form-item label="名称">
          <el-input v-model="createForm.name" maxlength="100" placeholder="请输入大屏名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" maxlength="255" placeholder="可选" />
        </el-form-item>
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="画布宽度">
              <el-input-number v-model="createForm.canvas_width" :min="600" :max="4096" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="画布高度">
              <el-input-number v-model="createForm.canvas_height" :min="360" :max="2160" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="主题">
          <el-select v-model="createForm.theme">
            <el-option label="light" value="light" />
            <el-option label="dark" value="dark" />
            <el-option label="tech-blue" value="tech-blue" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="createDialog.submitting" @click="submitCreateDashboard">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="bindingAssistantDialog.visible"
      title="属性绑定助手"
      width="760px"
      top="6vh"
      destroy-on-close
    >
      <div v-if="selectedComponent">
        <el-alert
          type="info"
          :closable="false"
          show-icon
          :title="`当前组件：${componentForm.title || defaultTitleByType(selectedComponent.type)}（${getTypeLabel(selectedComponent.type)}）`"
        />
        <el-divider />

        <el-form label-position="top">
          <el-divider content-position="left">基础属性</el-divider>
          <el-form-item label="标题">
            <el-input v-model="componentForm.title" maxlength="100" @change="handleSelectedMetaChange" />
          </el-form-item>
          <el-form-item label="绑定数据集">
            <el-select
              v-model="componentForm.dataset_id"
              clearable
              filterable
              placeholder="不绑定"
              @change="handleSelectedMetaChange"
            >
              <el-option
                v-for="item in datasetList"
                :key="`dialog-dataset-${item.id}`"
                :label="`${item.name} (ID:${item.id})`"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-row :gutter="8">
            <el-col :span="12">
              <el-form-item label="X">
                <el-input-number
                  v-model="componentForm.x"
                  :min="0"
                  :max="editor.canvasWidth"
                  :disabled="componentForm.locked"
                  @change="handleSelectedGeometryChange"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="Y">
                <el-input-number
                  v-model="componentForm.y"
                  :min="0"
                  :max="editor.canvasHeight"
                  :disabled="componentForm.locked"
                  @change="handleSelectedGeometryChange"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="8">
            <el-col :span="12">
              <el-form-item label="宽度">
                <el-input-number
                  v-model="componentForm.w"
                  :min="120"
                  :max="2400"
                  :disabled="componentForm.locked"
                  @change="handleSelectedGeometryChange"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="高度">
                <el-input-number
                  v-model="componentForm.h"
                  :min="80"
                  :max="1600"
                  :disabled="componentForm.locked"
                  @change="handleSelectedGeometryChange"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="层级 (z-index)">
            <el-input-number
              v-model="componentForm.z_index"
              :min="1"
              :max="999"
              :disabled="componentForm.locked"
              @change="handleSelectedGeometryChange"
            />
          </el-form-item>

          <el-divider content-position="left">外观与内容</el-divider>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="主色">
                <el-color-picker v-model="componentForm.color" show-alpha />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="锁定组件">
                <el-switch
                  v-model="componentForm.locked"
                  active-text="已锁定"
                  inactive-text="可编辑"
                  @change="handleSelectedConfigChange(false)"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item v-if="selectedComponent.type === 'line'" label="折线点（x,y，0-100；分号分隔）">
            <el-input
              v-model="componentForm.line_points_text"
              type="textarea"
              :rows="3"
              placeholder="示例：0,78; 20,42; 42,56; 60,30; 78,46; 100,22"
            />
          </el-form-item>
          <el-form-item v-if="selectedComponent.type === 'bar'" label="柱状高度（逗号分隔）">
            <el-input v-model="componentForm.bar_values_text" placeholder="示例：35,54,76,48,66" />
          </el-form-item>
          <el-form-item v-if="selectedComponent.type === 'pie'" label="饼图分片（名称:值，逗号分隔）">
            <el-input v-model="componentForm.pie_slices_text" placeholder="示例：A:40,B:30,C:30" />
          </el-form-item>
          <el-form-item v-if="selectedComponent.type === 'table'" label="表格行（每行一项）">
            <el-input
              v-model="componentForm.table_rows_text"
              type="textarea"
              :rows="4"
              placeholder="示例：华北&#10;华东&#10;华南&#10;西南"
            />
          </el-form-item>
          <el-form-item v-if="selectedComponent.type === 'treemap'" label="Treemap 权重（逗号分隔）">
            <el-input v-model="componentForm.treemap_weights_text" placeholder="示例：34,20,17,14,15" />
          </el-form-item>

          <el-divider content-position="left">字段绑定助手</el-divider>
          <el-form-item label="类别字段">
            <el-select v-model="componentForm.binding_category_field" clearable filterable placeholder="自动或手动选择">
              <el-option v-for="field in selectedDatasetFieldMeta.fields" :key="`cat-${field}`" :label="field" :value="field" />
            </el-select>
          </el-form-item>
          <el-form-item label="数值字段">
            <el-select v-model="componentForm.binding_value_field" clearable filterable placeholder="自动或手动选择">
              <el-option v-for="field in selectedDatasetFieldMeta.numericFields" :key="`val-${field}`" :label="field" :value="field" />
              <el-option
                v-for="field in selectedDatasetFieldMeta.fields.filter((item) => !selectedDatasetFieldMeta.numericFields.includes(item))"
                :key="`val-fallback-${field}`"
                :label="field"
                :value="field"
              />
            </el-select>
          </el-form-item>
          <el-row :gutter="8">
            <el-col :span="12">
              <el-form-item label="X 轴字段">
                <el-select v-model="componentForm.binding_x_field" clearable filterable placeholder="可选">
                  <el-option v-for="field in selectedDatasetFieldMeta.fields" :key="`x-${field}`" :label="field" :value="field" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="Y 轴字段">
                <el-select v-model="componentForm.binding_y_field" clearable filterable placeholder="可选">
                  <el-option v-for="field in selectedDatasetFieldMeta.numericFields" :key="`y-${field}`" :label="field" :value="field" />
                  <el-option
                    v-for="field in selectedDatasetFieldMeta.fields.filter((item) => !selectedDatasetFieldMeta.numericFields.includes(item))"
                    :key="`y-fallback-${field}`"
                    :label="field"
                    :value="field"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="系列字段（可选）">
            <el-select v-model="componentForm.binding_series_field" clearable filterable placeholder="可选">
              <el-option v-for="field in selectedDatasetFieldMeta.dimensionFields" :key="`series-${field}`" :label="field" :value="field" />
            </el-select>
          </el-form-item>

          <el-form-item label="绑定扩展配置（JSON）">
            <el-input
              v-model="componentForm.binding_json_text"
              type="textarea"
              :rows="4"
              placeholder='示例：{"xField":"date","yField":"sales"}'
            />
          </el-form-item>
        </el-form>

        <div class="assistant-actions">
          <el-button size="small" @click="autoFillBindingFields">自动映射字段</el-button>
          <el-button size="small" @click="applyBindingFieldsFromForm(true)">应用字段绑定</el-button>
          <el-button size="small" @click="openBoundDatasetPreview">查看数据预览</el-button>
          <el-button type="primary" size="small" @click="applyAllFromAssistant(false)">应用全部配置</el-button>
        </div>
      </div>
      <div v-else class="empty-note">请先在画布中选择一个组件，再打开属性绑定助手。</div>

      <template #footer>
        <el-button @click="bindingAssistantDialog.visible = false">关闭</el-button>
        <el-button type="primary" :disabled="!selectedComponent" @click="applyAllFromAssistant(true)">应用并关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="dataPreviewDialog.visible"
      :title="`绑定数据预览 - ${dataPreviewDialog.datasetName}`"
      width="78%"
      top="8vh"
      destroy-on-close
    >
      <div class="dataset-preview-meta">
        <span>总行数：{{ dataPreviewDialog.totalRows }}</span>
        <span>预览行数：{{ dataPreviewDialog.previewCount }}</span>
      </div>
      <el-table :data="dataPreviewDialog.rows" border height="420">
        <el-table-column type="index" label="#" width="64" />
        <el-table-column
          v-for="column in dataPreviewDialog.columns"
          :key="`dialog-${column}`"
          :prop="column"
          :label="column"
          min-width="140"
          show-overflow-tooltip
        />
      </el-table>
    </el-dialog>
  </div>
</template>
