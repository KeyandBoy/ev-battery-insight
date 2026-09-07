<template>
  <div class="viz-shell">
    <div class="chart-header">
      <div>
        <h3>区域统计表格</h3>
        <p>各区域样本量、平均密度、特征离散度及主类别标签一览。</p>
      </div>
    </div>
    <el-table :data="tableData" size="small" height="260" :row-class-name="rowClass">
      <el-table-column label="区域" width="80">
        <template #default="{ row }">
          <span :style="{ color: row.color, fontWeight: 700 }">
            {{ row.regionId === -1 ? "噪声" : `区域 ${row.regionId}` }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="size" label="样本数" width="78" />
      <el-table-column label="占比" width="72">
        <template #default="{ row }">{{ row.ratio }}</template>
      </el-table-column>
      <el-table-column label="平均密度" width="94">
        <template #default="{ row }">{{ row.densityMean }}</template>
      </el-table-column>
      <el-table-column label="特征离散度" width="100">
        <template #default="{ row }">{{ row.featureSpread }}</template>
      </el-table-column>
      <el-table-column label="主类别标签" min-width="130">
        <template #default="{ row }">
          <span v-if="row.topLabel">
            <el-tag size="small" :color="row.color" style="color:#fff;border:none">{{ row.topLabel }}</el-tag>
            <span style="margin-left:6px;color:#7d8ea0">{{ row.topRatio }}</span>
          </span>
          <span v-else style="color:#bcc9d5">—</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { computed } from "vue";
import * as d3 from "d3";

const props = defineProps({
  regions: { type: Array, default: () => [] }
});

const colorScale = d3.scaleOrdinal(d3.schemeTableau10);
const totalSamples = computed(() => props.regions.reduce((s, r) => s + r.size, 0));

const tableData = computed(() =>
  props.regions.map(r => {
    const dist = r.labelDistribution || {};
    const topEntry = Object.entries(dist).sort((a, b) => b[1] - a[1])[0];
    return {
      regionId: r.regionId,
      size: r.size,
      ratio: totalSamples.value ? `${((r.size / totalSamples.value) * 100).toFixed(1)}%` : "—",
      densityMean: (r.densityMean ?? 0).toFixed(4),
      featureSpread: (r.featureSpread ?? 0).toFixed(4),
      topLabel: topEntry?.[0] ?? null,
      topRatio: topEntry ? `${(topEntry[1] * 100).toFixed(1)}%` : null,
      color: r.regionId === -1 ? "#95a5a6" : colorScale(r.regionId)
    };
  })
);

function rowClass({ row }) {
  return row.regionId === -1 ? "noise-row" : "";
}
</script>
