<template>
  <div ref="containerRef" class="viz-shell">
    <div class="chart-header">
      <div>
        <h3>标签分布马赛克图</h3>
        <p>以面积比例展示各类别占比，矩形宽度对应样本占比，便于识别类别不均衡程度。</p>
      </div>
    </div>
    <svg ref="svgRef" class="chart-svg" style="height:260px"></svg>
  </div>
</template>

<script setup>
import * as d3 from "d3";
import { ref, watch } from "vue";
import { useResizeObserver } from "../../composables/region/useResizeObserver";

const props = defineProps({
  distribution: { type: Object, default: () => ({}) }
});

const containerRef = ref(null);
const svgRef = ref(null);

function render() {
  const svg = d3.select(svgRef.value);
  const width = containerRef.value?.clientWidth || 500;
  const height = 260;
  svg.attr("viewBox", `0 0 ${width} ${height}`).selectAll("*").remove();

  const entries = Object.entries(props.distribution);
  if (!entries.length) {
    svg.append("text")
      .attr("x", width / 2).attr("y", height / 2)
      .attr("text-anchor", "middle").attr("fill", "#60758a").attr("font-size", "13px")
      .text("该数据集没有标签列");
    return;
  }

  const sorted = [...entries].sort((a, b) => b[1] - a[1]);
  const color = d3.scaleOrdinal(d3.schemeTableau10).domain(sorted.map(e => e[0]));
  const total = sorted.reduce((s, [, v]) => s + v, 0);

  const barTop = 20;
  const barHeight = 160;
  const gap = 2;
  const usableWidth = width - gap * sorted.length;

  let curX = 0;
  sorted.forEach(([label, ratio]) => {
    const w = Math.max(1, (ratio / total) * usableWidth);

    svg.append("rect")
      .attr("x", curX).attr("y", barTop)
      .attr("width", w).attr("height", barHeight)
      .attr("fill", color(label))
      .attr("rx", Math.min(4, w / 3))
      .attr("opacity", 0.84);

    if (w > 28) {
      svg.append("text")
        .attr("x", curX + w / 2).attr("y", barTop + barHeight / 2 - 9)
        .attr("text-anchor", "middle").attr("fill", "#fff")
        .attr("font-size", w > 60 ? "12px" : "10px").attr("font-weight", "600")
        .text(String(label).length > 10 ? String(label).slice(0, 9) + "…" : label);
      svg.append("text")
        .attr("x", curX + w / 2).attr("y", barTop + barHeight / 2 + 10)
        .attr("text-anchor", "middle").attr("fill", "rgba(255,255,255,0.9)")
        .attr("font-size", "11px")
        .text(`${(ratio * 100).toFixed(1)}%`);
    }

    // tick below bar
    svg.append("line")
      .attr("x1", curX + w / 2).attr("y1", barTop + barHeight + 4)
      .attr("x2", curX + w / 2).attr("y2", barTop + barHeight + 8)
      .attr("stroke", color(label)).attr("stroke-width", 1.5);

    curX += w + gap;
  });

  // legend row
  const legendY = barTop + barHeight + 22;
  const legendItemW = Math.min(100, width / sorted.length);
  sorted.forEach(([label, ratio], i) => {
    const lx = i * legendItemW;
    if (lx + legendItemW > width) return;
    svg.append("rect")
      .attr("x", lx).attr("y", legendY).attr("width", 10).attr("height", 10)
      .attr("fill", color(label)).attr("rx", 2);
    svg.append("text")
      .attr("x", lx + 14).attr("y", legendY + 9)
      .attr("fill", "#5a6b7a").attr("font-size", "10px")
      .text(`${String(label).slice(0, 8)} ${(ratio * 100).toFixed(0)}%`);
  });
}

watch(() => props.distribution, render, { deep: true });
useResizeObserver(containerRef, render);
</script>
