<template>
  <div ref="containerRef" class="viz-shell">
    <div class="chart-header">
      <div>
        <h3>特征方差柱状图</h3>
        <p>数值维度中方差最高的特征排名，方差越大说明该维度区分度越强。</p>
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
  features: { type: Array, default: () => [] }
});

const containerRef = ref(null);
const svgRef = ref(null);

function render() {
  const svg = d3.select(svgRef.value);
  const width = containerRef.value?.clientWidth || 500;
  const height = 260;
  svg.attr("viewBox", `0 0 ${width} ${height}`);
  svg.selectAll("*").remove();

  if (!props.features.length) {
    svg.append("text")
      .attr("x", width / 2).attr("y", height / 2)
      .attr("text-anchor", "middle").attr("fill", "#60758a").attr("font-size", "13px")
      .text("选择数据集后显示特征方差分布");
    return;
  }

  const margin = { top: 12, right: 40, bottom: 12, left: 120 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  const data = [...props.features].sort((a, b) => a.variance - b.variance);
  const maxVal = d3.max(data, d => d.variance);
  const x = d3.scaleLinear().domain([0, maxVal]).range([0, innerWidth]);
  const y = d3.scaleBand().domain(data.map(d => d.column)).range([innerHeight, 0]).padding(0.3);
  const colorScale = d3.scaleSequential(d3.interpolateBlues).domain([0, maxVal]);

  g.append("g")
    .call(d3.axisLeft(y).tickSize(0))
    .call(ax => ax.selectAll("text").attr("fill", "#5a6b7a").attr("font-size", "11px"))
    .call(ax => ax.select(".domain").remove());

  g.selectAll("rect")
    .data(data).join("rect")
    .attr("y", d => y(d.column))
    .attr("height", y.bandwidth())
    .attr("x", 0)
    .attr("width", d => x(d.variance))
    .attr("fill", d => colorScale(d.variance))
    .attr("rx", 3)
    .append("title")
    .text(d => `${d.column}\n方差: ${d.variance.toFixed(4)}\n均值: ${d.mean.toFixed(4)}`);

  g.selectAll(".bar-label")
    .data(data).join("text").attr("class", "bar-label")
    .attr("x", d => x(d.variance) + 6)
    .attr("y", d => y(d.column) + y.bandwidth() / 2)
    .attr("dy", "0.35em")
    .attr("fill", "#4a5d6e").attr("font-size", "11px")
    .text(d => d.variance.toFixed(2));
}

watch(() => props.features, render, { deep: true });
useResizeObserver(containerRef, render);
</script>
