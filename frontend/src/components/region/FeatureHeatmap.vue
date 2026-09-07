<template>
  <div ref="containerRef" class="viz-shell">
    <div class="chart-header">
      <div>
        <h3>特征相关性像素图</h3>
        <p>相关系数矩阵热力图，蓝色表示正相关，红色表示负相关，对角线为自相关（=1）。</p>
      </div>
    </div>
    <svg ref="svgRef" class="chart-svg"></svg>
  </div>
</template>

<script setup>
import * as d3 from "d3";
import { ref, watch } from "vue";
import { useResizeObserver } from "../../composables/region/useResizeObserver";

const props = defineProps({
  correlation: { type: Object, default: () => ({}) }
});

const containerRef = ref(null);
const svgRef = ref(null);

function render() {
  const svg = d3.select(svgRef.value);
  const width = containerRef.value?.clientWidth || 500;
  const features = Object.keys(props.correlation);

  if (!features.length) {
    const h = 260;
    svg.attr("viewBox", `0 0 ${width} ${h}`).selectAll("*").remove();
    svg.append("text")
      .attr("x", width / 2).attr("y", h / 2)
      .attr("text-anchor", "middle").attr("fill", "#60758a").attr("font-size", "13px")
      .text("运行分析后将在这里展示特征相关性像素图");
    return;
  }

  const n = features.length;
  const margin = { top: 10, right: 20, bottom: 90, left: 90 };
  const maxCell = Math.floor((width - margin.left - margin.right) / n);
  const cellSize = Math.max(10, Math.min(46, maxCell));
  const innerSize = cellSize * n;
  const height = innerSize + margin.top + margin.bottom;

  svg.attr("viewBox", `0 0 ${width} ${height}`).selectAll("*").remove();

  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
  const colorScale = d3.scaleDiverging(d3.interpolateRdBu).domain([-1, 0, 1]);

  features.forEach((rowFeat, ri) => {
    features.forEach((colFeat, ci) => {
      const val = props.correlation[rowFeat]?.[colFeat] ?? 0;
      g.append("rect")
        .attr("x", ci * cellSize).attr("y", ri * cellSize)
        .attr("width", cellSize - 1).attr("height", cellSize - 1)
        .attr("fill", colorScale(val))
        .append("title")
        .text(`${rowFeat} × ${colFeat}: ${val.toFixed(3)}`);

      if (cellSize >= 26) {
        g.append("text")
          .attr("x", ci * cellSize + cellSize / 2)
          .attr("y", ri * cellSize + cellSize / 2)
          .attr("dy", "0.35em").attr("text-anchor", "middle")
          .attr("font-size", cellSize >= 38 ? "10px" : "8px")
          .attr("fill", Math.abs(val) > 0.55 ? "#fff" : "#334")
          .text(val.toFixed(2));
      }
    });
  });

  // x-axis labels (rotated)
  g.append("g").selectAll("text").data(features).join("text")
    .attr("x", (_, i) => i * cellSize + cellSize / 2)
    .attr("y", innerSize + 10)
    .attr("text-anchor", "start")
    .attr("transform", (_, i) => `rotate(-40, ${i * cellSize + cellSize / 2}, ${innerSize + 10})`)
    .attr("fill", "#5a6b7a").attr("font-size", "10px")
    .text(d => d.length > 9 ? d.slice(0, 8) + "…" : d);

  // y-axis labels
  g.append("g").selectAll("text").data(features).join("text")
    .attr("x", -6).attr("y", (_, i) => i * cellSize + cellSize / 2)
    .attr("dy", "0.35em").attr("text-anchor", "end")
    .attr("fill", "#5a6b7a").attr("font-size", "10px")
    .text(d => d.length > 9 ? d.slice(0, 8) + "…" : d);

  // color legend bar
  const legendW = Math.min(180, innerSize);
  const legendX = 0;
  const legendY = innerSize + margin.bottom - 20;
  const defs = svg.append("defs");
  const gradId = "heatmap-grad";
  const grad = defs.append("linearGradient").attr("id", gradId);
  grad.selectAll("stop")
    .data(d3.range(-1, 1.01, 0.25)).join("stop")
    .attr("offset", d => `${((d + 1) / 2) * 100}%`)
    .attr("stop-color", d => colorScale(d));

  const lg = svg.append("g").attr("transform", `translate(${margin.left + legendX}, ${margin.top + legendY})`);
  lg.append("rect").attr("width", legendW).attr("height", 8).attr("rx", 3)
    .attr("fill", `url(#${gradId})`);
  lg.append("text").attr("x", 0).attr("y", 18).attr("fill", "#5a6b7a").attr("font-size", "9px").text("-1");
  lg.append("text").attr("x", legendW / 2).attr("y", 18).attr("text-anchor", "middle")
    .attr("fill", "#5a6b7a").attr("font-size", "9px").text("0");
  lg.append("text").attr("x", legendW).attr("y", 18).attr("text-anchor", "end")
    .attr("fill", "#5a6b7a").attr("font-size", "9px").text("+1");
}

watch(() => props.correlation, render, { deep: true });
useResizeObserver(containerRef, render);
</script>
