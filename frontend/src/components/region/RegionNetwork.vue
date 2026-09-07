<template>
  <div ref="containerRef" class="viz-shell">
    <div class="chart-header">
      <div>
        <h3>区域关联网络</h3>
        <p>基于区域中心距离和规模权重构建跨区域关联图，用于分析区域之间的结构关系。</p>
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
import { onBeforeUnmount, ref, watch } from "vue";
import { useResizeObserver } from "../../composables/region/useResizeObserver";
import { exportSvg, exportSvgAsPng } from "../../utils/region/chartExport";

const props = defineProps({
  regions: { type: Array, default: () => [] },
  links: { type: Array, default: () => [] },
  selectedRegion: { type: Number, default: null }
});

const emit = defineEmits(["select-region"]);

const containerRef = ref(null);
const svgRef = ref(null);
let simulationInstance = null;

function render() {
  if (simulationInstance) {
    simulationInstance.stop();
    simulationInstance = null;
  }
  const svg = d3.select(svgRef.value);
  const width = containerRef.value?.clientWidth || svgRef.value?.clientWidth || 600;
  const height = 380;
  svg.attr("viewBox", `0 0 ${width} ${height}`);
  svg.selectAll("*").remove();

  if (!props.regions.length) {
    svg
      .append("text")
      .attr("x", width / 2)
      .attr("y", height / 2)
      .attr("text-anchor", "middle")
      .attr("fill", "#60758a")
      .text("暂无区域网络数据");
    return;
  }

  const nodes = props.regions.map((region) => ({ ...region }));
  const links = props.links.map((link) => ({ ...link }));
  const color = d3.scaleOrdinal(d3.schemeTableau10);
  const simulation = d3
    .forceSimulation(nodes)
    .force("link", d3.forceLink(links).id((d) => d.regionId).distance((d) => 60 + d.distance * 10))
    .force("charge", d3.forceManyBody().strength(-120))
    .force("center", d3.forceCenter(width / 2, height / 2));
  simulationInstance = simulation;

  const link = svg
    .append("g")
    .selectAll("line")
    .data(links)
    .join("line")
    .attr("stroke", "#9ab0c4")
    .attr("stroke-opacity", 0.6)
    .attr("stroke-width", (d) => Math.max(1, Math.min(4, d.weight / 80)));

  const node = svg
    .append("g")
    .selectAll("circle")
    .data(nodes)
    .join("circle")
    .attr("r", (d) => 8 + Math.sqrt(d.size))
    .attr("fill", (d) => color(d.regionId))
    .attr("stroke", (d) => (props.selectedRegion === d.regionId ? "#10253a" : "#ffffff"))
    .attr("stroke-width", (d) => (props.selectedRegion === d.regionId ? 3 : 1.5))
    .style("cursor", "pointer");

  const labels = svg
    .append("g")
    .selectAll("text")
    .data(nodes)
    .join("text")
    .text((d) => `R${d.regionId}`)
    .attr("font-size", 12)
    .attr("fill", "#173047")
    .attr("text-anchor", "middle")
    .attr("dy", 4);

  node.append("title").text((d) => `区域 ${d.regionId}\n规模 ${d.size}`);
  node.on("click", (_, datum) => {
    emit("select-region", datum.regionId);
  });

  simulation.on("tick", () => {
    link
      .attr("x1", (d) => d.source.x)
      .attr("y1", (d) => d.source.y)
      .attr("x2", (d) => d.target.x)
      .attr("y2", (d) => d.target.y);
    node.attr("cx", (d) => d.x).attr("cy", (d) => d.y);
    labels.attr("x", (d) => d.x).attr("y", (d) => d.y);
  });
}

watch(() => [props.regions, props.links, props.selectedRegion], render, { deep: true });
useResizeObserver(containerRef, render);
onBeforeUnmount(() => {
  if (simulationInstance) {
    simulationInstance.stop();
    simulationInstance = null;
  }
});

function handleExportSvg() {
  exportSvg(svgRef.value, "region-network.svg");
}

function handleExportPng() {
  exportSvgAsPng(svgRef.value, "region-network.png");
}
</script>
