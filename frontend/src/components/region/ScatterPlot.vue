<template>
  <div ref="containerRef" class="viz-shell">
    <div class="chart-header">
      <div>
        <h3>区域嵌入散点图</h3>
        <p>支持局部区域选中、Voronoi 边界显示和密度着色，用于观察区域在低维空间中的分布。</p>
      </div>
      <div class="action-row">
        <button class="ghost-button" @click="handleExportSvg">导出 SVG</button>
        <button class="ghost-button" @click="handleExportPng">导出 PNG</button>
        <button class="ghost-button" @click="$emit('select-region', null)">清除选区</button>
      </div>
    </div>
    <svg ref="svgRef" class="chart-svg"></svg>
  </div>
</template>

<script setup>
import * as d3 from "d3";
import { ref, watch } from "vue";
import { useResizeObserver } from "../../composables/region/useResizeObserver";
import { exportSvg, exportSvgAsPng } from "../../utils/region/chartExport";

const props = defineProps({
  points: { type: Array, default: () => [] },
  polygons: { type: Array, default: () => [] },
  regions: { type: Array, default: () => [] },
  selectedRegion: { type: Number, default: null }
});

const emit = defineEmits(["select-region"]);

const containerRef = ref(null);
const svgRef = ref(null);

function render() {
  const svg = d3.select(svgRef.value);
  const width = containerRef.value?.clientWidth || svgRef.value?.clientWidth || 820;
  const height = 430;
  svg.attr("viewBox", `0 0 ${width} ${height}`);
  svg.selectAll("*").remove();

  if (!props.points.length) {
    svg
      .append("text")
      .attr("x", width / 2)
      .attr("y", height / 2)
      .attr("text-anchor", "middle")
      .attr("fill", "#60758a")
      .text("运行分析后将在这里展示区域散点图");
    return;
  }

  const margin = { top: 18, right: 18, bottom: 44, left: 44 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const group = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  const x = d3.scaleLinear().domain(d3.extent(props.points, (d) => d.x)).nice().range([0, innerWidth]);
  const y = d3.scaleLinear().domain(d3.extent(props.points, (d) => d.y)).nice().range([innerHeight, 0]);
  const color = d3.scaleOrdinal(d3.schemeTableau10);

  group
    .append("g")
    .attr("transform", `translate(0,${innerHeight})`)
    .call(d3.axisBottom(x).ticks(6))
    .call((axis) => axis.selectAll("text").attr("fill", "#7d8ea0"))
    .call((axis) => axis.selectAll("line,path").attr("stroke", "#bcc9d5"));

  group
    .append("g")
    .call(d3.axisLeft(y).ticks(6))
    .call((axis) => axis.selectAll("text").attr("fill", "#7d8ea0"))
    .call((axis) => axis.selectAll("line,path").attr("stroke", "#bcc9d5"));

  const line = d3.line().x((d) => x(d[0])).y((d) => y(d[1]));
  group
    .append("g")
    .selectAll("path")
    .data(props.polygons)
    .join("path")
    .attr("d", (polygon) => line([...polygon.points, polygon.points[0]]))
    .attr("fill", (polygon) => color(polygon.regionId))
    .attr("fill-opacity", (polygon) => (props.selectedRegion === null || props.selectedRegion === polygon.regionId ? 0.12 : 0.04))
    .attr("stroke", (polygon) => color(polygon.regionId))
    .attr("stroke-width", (polygon) => (props.selectedRegion === polygon.regionId ? 2.5 : 1.2))
    .attr("stroke-opacity", 0.55);

  const densityExtent = d3.extent(props.points, (d) => d.density);
  const radius = d3.scaleSqrt().domain(densityExtent).range([3, 8]);

  group
    .append("g")
    .selectAll("circle")
    .data(props.points)
    .join("circle")
    .attr("cx", (d) => x(d.x))
    .attr("cy", (d) => y(d.y))
    .attr("r", (d) => radius(d.density))
    .attr("fill", (d) => (d.region === -1 ? "#95a5a6" : color(d.region)))
    .attr("fill-opacity", (d) => (props.selectedRegion === null || props.selectedRegion === d.region ? 0.82 : 0.14))
    .attr("stroke", (d) => (props.selectedRegion === d.region ? "#10253a" : "transparent"))
    .attr("stroke-width", 1.2)
    .style("cursor", "pointer")
    .append("title")
    .text((d) => `样本 ${d.id}\n区域 ${d.region}\n密度 ${d.density.toFixed(4)}`);

  group
    .selectAll("circle")
    .on("click", (_, datum) => {
      emit("select-region", datum.region);
    });

  group
    .append("text")
    .attr("x", innerWidth / 2)
    .attr("y", innerHeight + 36)
    .attr("text-anchor", "middle")
    .attr("fill", "#6b7e92")
    .text("降维轴 X");

  group
    .append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -innerHeight / 2)
    .attr("y", -30)
    .attr("text-anchor", "middle")
    .attr("fill", "#6b7e92")
    .text("降维轴 Y");
}

watch(() => [props.points, props.polygons, props.selectedRegion], render, { deep: true });
useResizeObserver(containerRef, render);

function handleExportSvg() {
  exportSvg(svgRef.value, "region-scatter.svg");
}

function handleExportPng() {
  exportSvgAsPng(svgRef.value, "region-scatter.png");
}
</script>
