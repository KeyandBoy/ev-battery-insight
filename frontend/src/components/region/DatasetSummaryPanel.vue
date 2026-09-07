<template>
  <div class="summary-panel">
    <div class="chart-header">
      <div>
        <h3>数据集统计摘要</h3>
        <p>从缺失分布、特征方差和标签占比三个角度快速评估数据质量与结构特征。</p>
      </div>
    </div>

    <div v-if="summary" class="summary-grid">
      <div class="mini-card">
        <strong>缺失概览</strong>
        <span>缺失单元 {{ summary.missingOverview?.totalMissingCells ?? 0 }}</span>
        <span>缺失行 {{ summary.missingOverview?.rowsWithMissing ?? 0 }}</span>
        <span>缺失列 {{ summary.missingOverview?.columnsWithMissing ?? 0 }}</span>
      </div>
      <div class="mini-card">
        <strong>特征概览</strong>
        <span>数值维度 {{ summary.featureOverview?.numericFeatureCount ?? 0 }}</span>
        <span>标签列 {{ summary.dataset?.labelColumn || "无" }}</span>
        <span>样本数 {{ summary.dataset?.sampleCount ?? 0 }}</span>
      </div>
      <div class="mini-card full-width">
        <strong>高方差特征</strong>
        <div v-if="summary.featureOverview?.topVarianceFeatures?.length" class="pill-grid">
          <span v-for="item in summary.featureOverview.topVarianceFeatures" :key="item.column" class="data-pill">
            {{ item.column }} / var {{ Number(item.variance).toFixed(2) }}
          </span>
        </div>
        <span v-else>暂无高方差特征数据</span>
      </div>
      <div class="mini-card full-width">
        <strong>标签分布</strong>
        <div v-if="labelEntries.length" class="pill-grid">
          <span v-for="[label, ratio] in labelEntries" :key="label" class="data-pill">
            {{ label }} : {{ percent(ratio) }}
          </span>
        </div>
        <span v-else>当前数据集没有可用的标签分布</span>
      </div>
      <div class="mini-card full-width">
        <strong>缺失最多的字段</strong>
        <div v-if="summary.missingOverview?.topMissingColumns?.length" class="pill-grid">
          <span v-for="item in summary.missingOverview.topMissingColumns" :key="item.column" class="data-pill warn">
            {{ item.column }} / {{ item.missingCount }} / {{ percent(item.missingRatio) }}
          </span>
        </div>
        <span v-else>当前数据集没有缺失字段</span>
      </div>
    </div>
    <p v-else class="empty-text">暂无数据集统计摘要</p>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  summary: { type: Object, default: null }
});

const labelEntries = computed(() => Object.entries(props.summary?.labelDistribution || {}));

function percent(value) {
  return `${(Number(value) * 100).toFixed(1)}%`;
}
</script>
