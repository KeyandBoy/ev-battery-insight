 <template>
  <div class="metrics-board">
    <div class="metrics-grid">
      <div class="metric-card">
        <h3>预处理摘要</h3>
        <p>输入样本 {{ preprocess?.inputRows ?? 0 }}</p>
        <p>输入维度 {{ preprocess?.inputDimensions ?? 0 }}</p>
        <p>输出维度 {{ preprocess?.outputDimensions ?? 0 }}</p>
        <p>缺失率 {{ format(preprocess?.missingRatio) }}</p>
      </div>
      <div class="metric-card">
        <h3>降维质量</h3>
        <p>方法 {{ reduction?.method ?? "-" }}</p>
        <p>可信度 {{ format(reduction?.trustworthiness) }}</p>
        <p>距离保持 {{ format(reduction?.distancePreservation) }}</p>
        <p>耗时 {{ ms(reduction?.elapsedMs) }}</p>
      </div>
      <div class="metric-card">
        <h3>聚类质量</h3>
        <p>轮廓系数 {{ format(quality?.silhouette) }}</p>
        <p>Davies-Bouldin {{ format(quality?.daviesBouldin) }}</p>
        <p>Calinski-Harabasz {{ format(quality?.calinskiHarabasz) }}</p>
        <p>区域均衡 {{ format(quality?.regionBalance) }}</p>
      </div>
      <div class="metric-card">
        <h3>性能指标</h3>
        <p>总耗时 {{ ms(performance?.totalElapsedMs) }}</p>
        <p>渲染点数 {{ performance?.pointsRendered ?? 0 }}</p>
        <p>参与维度 {{ performance?.dimensionsUsed ?? 0 }}</p>
        <p>噪声比例 {{ format(quality?.noiseRatio) }}</p>
      </div>
    </div>

    <div class="runs-panel">
      <div class="section-split">
        <div>
          <h3>最近运行</h3>
          <p>点击历史运行可直接回放该次分析结果，并同步参数到当前工作台。</p>
        </div>
      </div>

      <div v-if="runs?.length" class="run-list run-list--compact">
        <button
          v-for="run in runs"
          :key="run.id"
          class="run-item run-button"
          :class="{ active: currentRunId === run.id }"
          @click="$emit('select-run', run.id)"
        >
          <strong>#{{ run.id }}</strong>
          <span>{{ run.datasetName || `数据集${run.datasetId}` }}</span>
          <span>{{ run.reducer }} / {{ run.algorithm }}</span>
          <span>保真 {{ format(run.preservationScore) }}</span>
        </button>
      </div>
      <p v-else class="empty-text">暂无历史记录</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  preprocess: { type: Object, default: null },
  reduction: { type: Object, default: null },
  quality: { type: Object, default: null },
  performance: { type: Object, default: null },
  runs: { type: Array, default: () => [] },
  currentRunId: { type: Number, default: null }
});

defineEmits(["select-run"]);

function format(value) {
  return value === null || value === undefined ? "-" : Number(value).toFixed(4);
}

function ms(value) {
  return value === null || value === undefined ? "-" : `${Number(value).toFixed(1)} ms`;
}
</script>
