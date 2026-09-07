<template>
  <div class="summary-layout">
    <div class="region-list">
      <div class="chart-header">
        <div>
          <h3>区域摘要</h3>
          <p>按区域查看规模、密度、扩散度与核心特征，帮助定位局部结构差异。</p>
        </div>
      </div>
      <div class="region-cards">
        <button
          v-for="region in regions"
          :key="region.regionId"
          class="region-card"
          :class="{ active: selectedRegion === region.regionId }"
          @click="$emit('select-region', region.regionId)"
        >
          <strong>区域 {{ region.regionId }}</strong>
          <span>样本数 {{ region.size }}</span>
          <span>平均密度 {{ region.densityMean.toFixed(4) }}</span>
          <span>扩散度 {{ region.featureSpread.toFixed(4) }}</span>
          <span v-if="topFeatureLabel(region)">主特征 {{ topFeatureLabel(region) }}</span>
        </button>
      </div>
    </div>
    <div class="correlation-panel">
      <div class="chart-header">
        <div>
          <h3>特征相关矩阵</h3>
          <p>展示当前高方差维度的相关性热力视图，用于观察区域结构的特征耦合关系。</p>
        </div>
      </div>
      <div v-if="correlationKeys.length" class="heatmap">
        <div class="heatmap-row heatmap-head">
          <span></span>
          <span v-for="column in correlationKeys" :key="column">{{ column }}</span>
        </div>
        <div v-for="rowKey in correlationKeys" :key="rowKey" class="heatmap-row">
          <span class="heatmap-label">{{ rowKey }}</span>
          <span
            v-for="column in correlationKeys"
            :key="`${rowKey}-${column}`"
            class="heatmap-cell"
            :style="{ background: cellColor(correlation[rowKey][column]) }"
          >
            {{ Number(correlation[rowKey][column]).toFixed(2) }}
          </span>
        </div>
      </div>
      <p v-else class="empty-text">暂无相关矩阵数据</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  regions: { type: Array, default: () => [] },
  correlation: { type: Object, default: () => ({}) },
  selectedRegion: { type: Number, default: null }
});

defineEmits(["select-region"]);

const correlationKeys = computed(() => Object.keys(props.correlation));

function topFeatureLabel(region) {
  if (!region?.topFeatureMeans) {
    return "";
  }
  const [feature, value] = Object.entries(region.topFeatureMeans).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))[0] || [];
  return feature ? `${feature}: ${Number(value).toFixed(2)}` : "";
}

function cellColor(value) {
  const number = Number(value);
  if (Number.isNaN(number)) {
    return "#eef3f7";
  }
  const alpha = Math.min(0.92, Math.abs(number));
  return number >= 0 ? `rgba(25, 121, 169, ${alpha})` : `rgba(214, 116, 75, ${alpha})`;
}
</script>
