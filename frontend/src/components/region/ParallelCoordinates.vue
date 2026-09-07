<template>
  <div ref="containerRef" class="viz-shell">
    <div class="chart-header">
      <div>
        <h3>平行坐标联动视图</h3>
        <p>展示高方差维度的局部与全局差异，区域选中后高亮对应折线。</p>
      </div>
      <div class="action-row">
        <button class="ghost-button" @click="handleExportSvg">导出 SVG</button>
        <button class="ghost-button" @click="handleExportPng">导出 PNG</button>
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
  dimensions: { type: Array, default: () => [] },
  records: { type: Array, default: () => [] },
  selectedRegion: { type: Number, default: null }
});

const containerRef = ref(null);
const svgRef = ref(null);

function render() {
  const svg = d3.select(svgRef.value);
  const width = containerRef.value?.clientWidth || svgRef.value?.clientWidth || 820;
  const height = 360;
  svg.attr("viewBox", `0 0 ${width} ${height}`);
  svg.selectAll("*").remove();

  if (!props.dimensions.length || !props.records.length) {
    svg
      .append("text")
      .attr("x", width / 2)
      .attr("y", height / 2)
      .attr("text-anchor", "middle")
      .attr("fill", "#60758a")
      .text("暂无平行坐标数据");
    return;
  }

  const margin = { top: 24, right: 28, bottom: 22, left: 28 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const root = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
  const x = d3.scalePoint().domain(props.dimensions).range([0, innerWidth]).padding(0.35);
  const yScales = new Map(
    props.dimensions.map((dimension) => [
      dimension,
      d3
        .scaleLinear()
        .domain(d3.extent(props.records, (row) => Number(row[dimension])))
        .nice()
        .range([innerHeight, 0])
    ])
  );
  const color = d3.scaleOrdinal(d3.schemeTableau10);
  const line = d3.line();

  root
    .append("g")
    .selectAll("path")
    .data(props.records)
    .join("path")
    .attr("d", (row) =>
      line(props.dimensions.map((dimension) => [x(dimension), yScales.get(dimension)(Number(row[dimension]))]))
    )
    .attr("fill", "none")
    .attr("stroke", (row) => (row.region === -1 ? "#a5afb8" : color(row.region)))
    .attr("stroke-opacity", (row) => (props.selectedRegion === null || props.selectedRegion === row.region ? 0.5 : 0.06))
    .attr("stroke-width", (row) => (props.selectedRegion === row.region ? 2.2 : 1));

  props.dimensions.forEach((dimension) => {
    const axisGroup = root.append("g").attr("transform", `translate(${x(dimension)},0)`);
    axisGroup
      .call(d3.axisLeft(yScales.get(dimension)).ticks(5))
      .call((axis) => axis.selectAll("text").attr("fill", "#708496"))
      .call((axis) => axis.selectAll("line,path").attr("stroke", "#bcc9d5"));
    axisGroup
      .append("text")
      .attr("y", -10)
      .attr("text-anchor", "middle")
      .attr("fill", "#203447")
      .style("font-size", "12px")
      .text(dimension);
  });
}

watch(() => [props.dimensions, props.records, props.selectedRegion], render, { deep: true });
useResizeObserver(containerRef, render);

function handleExportSvg() {
  exportSvg(svgRef.value, "parallel-coordinates.svg");
}

function handleExportPng() {
  exportSvgAsPng(svgRef.value, "parallel-coordinates.png");
}
</script>
