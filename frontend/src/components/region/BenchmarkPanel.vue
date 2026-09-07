<template>
  <div class="benchmark-panel">
    <div class="section-head">
      <div>
        <h2>批量性能基准测试</h2>
        <p>针对当前数据集批量运行多种降维与聚类组合，对比速度、保真度和聚类质量。</p>
      </div>
      <button class="primary-button" @click="$emit('run')" :disabled="loading || !datasetId">
        {{ loading ? "测试中..." : "运行基准测试" }}
      </button>
    </div>

    <div class="compare-selectors">
      <label>
        重复次数
        <input :value="repeats" type="number" min="1" max="6" @input="updateRepeats($event.target.value)" />
      </label>
      <div class="mini-card">
        <strong>当前数据集</strong>
        <span>{{ datasetId || "未选择" }}</span>
      </div>
    </div>

    <div v-if="result" class="benchmark-grid">
      <div class="mini-card">
        <strong>最快场景</strong>
        <span>{{ result.summary?.fastestLabel || "-" }}</span>
        <span>{{ formatMs(result.summary?.fastestElapsedMs) }}</span>
      </div>
      <div class="mini-card">
        <strong>最佳保真</strong>
        <span>{{ result.summary?.bestQualityLabel || "-" }}</span>
        <span>{{ format(result.summary?.bestQualityScore) }}</span>
      </div>
      <div class="mini-card full-width">
        <strong>场景结果</strong>
        <div class="compare-table">
          <div class="compare-row compare-head benchmark-row">
            <span>场景</span>
            <span>平均耗时</span>
            <span>平均保真</span>
            <span>平均轮廓</span>
            <span>平均噪声</span>
          </div>
          <div v-for="item in result.results" :key="item.label" class="compare-row benchmark-row">
            <span>{{ item.label }}</span>
            <span>{{ formatMs(item.aggregate.totalElapsedMsMean) }}</span>
            <span>{{ format(item.aggregate.preservationScoreMean) }}</span>
            <span>{{ format(item.aggregate.silhouetteMean) }}</span>
            <span>{{ format(item.aggregate.noiseRatioMean) }}</span>
          </div>
        </div>
      </div>
    </div>
    <p v-else class="empty-text">运行后将在这里展示批量基准测试结果</p>
  </div>
</template>

<script setup>
defineProps({
  datasetId: { type: Number, default: null },
  repeats: { type: Number, default: 2 },
  loading: { type: Boolean, default: false },
  result: { type: Object, default: null }
});

const emit = defineEmits(["run", "update:repeats"]);

function format(value) {
  return value === null || value === undefined ? "-" : Number(value).toFixed(4);
}

function formatMs(value) {
  return value === null || value === undefined ? "-" : `${Number(value).toFixed(1)} ms`;
}

function updateRepeats(value) {
  const parsed = Number(value);
  const repeats = Number.isFinite(parsed) ? Math.min(6, Math.max(1, parsed)) : 2;
  emit("update:repeats", repeats);
}
</script>
