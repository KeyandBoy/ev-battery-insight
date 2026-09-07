<template>
  <div class="comparison-panel">
    <div class="section-head">
      <div>
        <h2>运行对比</h2>
        <p>选择两次分析结果，比较保真度、聚类质量和性能表现。</p>
      </div>
      <button class="secondary-button" @click="$emit('compare')" :disabled="validRunCount < 2">
        生成对比
      </button>
    </div>

    <div class="compare-selectors">
      <label>
        左侧运行
        <select :value="selectedRunIds[0] ?? ''" @change="updateSelection(0, $event.target.value)">
          <option value="">请选择</option>
          <option v-for="run in runs" :key="`left-${run.id}`" :value="run.id">
            #{{ run.id }} / {{ run.datasetName || `数据集${run.datasetId}` }} / {{ run.reducer }} / {{ run.algorithm }}
          </option>
        </select>
      </label>
      <label>
        右侧运行
        <select :value="selectedRunIds[1] ?? ''" @change="updateSelection(1, $event.target.value)">
          <option value="">请选择</option>
          <option v-for="run in runs" :key="`right-${run.id}`" :value="run.id">
            #{{ run.id }} / {{ run.datasetName || `数据集${run.datasetId}` }} / {{ run.reducer }} / {{ run.algorithm }}
          </option>
        </select>
      </label>
    </div>

    <div v-if="comparison" class="comparison-grid">
      <div class="mini-card">
        <strong>左侧</strong>
        <span>#{{ comparison.left.id }}</span>
        <span>{{ comparison.left.reducer }} / {{ comparison.left.algorithm }}</span>
      </div>
      <div class="mini-card">
        <strong>右侧</strong>
        <span>#{{ comparison.right.id }}</span>
        <span>{{ comparison.right.reducer }} / {{ comparison.right.algorithm }}</span>
      </div>
      <div class="mini-card full-width">
        <strong>指标差异</strong>
        <div class="compare-table" v-if="metricEntries.length">
          <div class="compare-row compare-head">
            <span>指标</span>
            <span>左侧</span>
            <span>右侧</span>
            <span>差值</span>
          </div>
          <div v-for="[key, item] in metricEntries" :key="key" class="compare-row">
            <span>{{ key }}</span>
            <span>{{ fmt(item.left) }}</span>
            <span>{{ fmt(item.right) }}</span>
            <span :class="{ positive: Number(item.delta) > 0, negative: Number(item.delta) < 0 }">
              {{ fmt(item.delta) }}
            </span>
          </div>
        </div>
      </div>
    </div>
    <p v-else class="empty-text">选择两条运行记录后即可生成对比结果</p>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  runs: { type: Array, default: () => [] },
  selectedRunIds: { type: Array, default: () => [] },
  comparison: { type: Object, default: null }
});

const emit = defineEmits(["update:selected-run-ids", "compare"]);

const metricEntries = computed(() => Object.entries(props.comparison?.metrics || {}));
const validRunCount = computed(() => props.selectedRunIds.filter(Boolean).length);

function updateSelection(index, value) {
  const next = [...props.selectedRunIds];
  next[index] = value ? Number(value) : null;
  emit("update:selected-run-ids", next);
}

function fmt(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return Number(value).toFixed(4);
}
</script>
