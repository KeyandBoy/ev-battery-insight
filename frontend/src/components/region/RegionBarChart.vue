<template>
  <div ref="containerRef" class="viz-shell">
    <div class="chart-header">
      <div>
        <h3>{{ mode === "stacked" ? "区域维度堆叠图" : "区域规模柱状图" }}</h3>
        <p>{{ mode === "stacked" ? "各区域按核心特征均值绝对值堆叠，揭示不同区域在特征空间中的组成差异。" : "各聚类区域的样本数量对比，噪声点标为灰色。" }}</p>
      </div>
      <div class="action-row">
        <button class="ghost-button" :style="mode === 'stacked' ? activeStyle : {}" @click="mode = 'stacked'">堆叠</button>
        <button class="ghost-button" :style="mode === 'size' ? activeStyle : {}" @click="mode = 'size'">规模</button>
      </div>
    </div>
    <svg ref="svgRef" class="chart-svg" style="height:300px"></svg>
  </div>
</template>

<script setup>
import * as d3 from "d3";
import { ref, watch } from "vue";
import { useResizeObserver } from "../../composables/region/useResizeObserver";

const props = defineProps({
  regions: { type: Array, default: () => [] }
});

const containerRef = ref(null);
const svgRef = ref(null);
const mode = ref("stacked");
const activeStyle = { borderColor: "var(--c-blue, #2d78b5)", color: "var(--c-blue, #2d78b5)" };

function render() {
  const svg = d3.select(svgRef.value);
  const width = containerRef.value?.clientWidth || 600;
  const height = 300;
  svg.attr("viewBox", `0 0 ${width} ${height}`).selectAll("*").remove();

  if (!props.regions.length) {
    svg.append("text")
      .attr("x", width / 2).attr("y", height / 2)
      .attr("text-anchor", "middle").attr("fill", "#60758a").attr("font-size", "13px")
      .text("运行分析后展示区域特征分布");
    return;
  }

  if (mode.value === "size") {
    renderSizeChart(svg, width, height);
  } else {
    renderStackedChart(svg, width, height);
  }
}

function renderSizeChart(svg, width, height) {
  const margin = { top: 18, right: 20, bottom: 44, left: 54 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  const colorNormal = d3.scaleOrdinal(d3.schemeTableau10);
  const data = props.regions;

  const x = d3.scaleBand()
    .domain(data.map(r => r.regionId === -1 ? "噪声" : `R${r.regionId}`))
    .range([0, innerW]).padding(0.32);
  const y = d3.scaleLinear().domain([0, d3.max(data, r => r.size)]).nice().range([innerH, 0]);

  g.append("g").attr("transform", `translate(0,${innerH})`)
    .call(d3.axisBottom(x))
    .call(ax => ax.selectAll("text").attr("fill", "#7d8ea0").attr("font-size", "11px"))
    .call(ax => ax.selectAll("line,path").attr("stroke", "#bcc9d5"));
  g.append("g")
    .call(d3.axisLeft(y).ticks(5))
    .call(ax => ax.selectAll("text").attr("fill", "#7d8ea0").attr("font-size", "11px"))
    .call(ax => ax.selectAll("line,path").attr("stroke", "#bcc9d5"));

  g.selectAll("rect").data(data).join("rect")
    .attr("x", r => x(r.regionId === -1 ? "噪声" : `R${r.regionId}`))
    .attr("y", r => y(r.size))
    .attr("width", x.bandwidth())
    .attr("height", r => innerH - y(r.size))
    .attr("fill", r => r.regionId === -1 ? "#95a5a6" : colorNormal(r.regionId))
    .attr("rx", 4).attr("opacity", 0.86)
    .append("title").text(r => `区域 ${r.regionId}: ${r.size} 样本`);

  g.selectAll(".size-val").data(data).join("text").attr("class", "size-val")
    .attr("x", r => x(r.regionId === -1 ? "噪声" : `R${r.regionId}`) + x.bandwidth() / 2)
    .attr("y", r => y(r.size) - 5)
    .attr("text-anchor", "middle").attr("fill", "#4a5d6e").attr("font-size", "11px")
    .text(r => r.size);
}

function renderStackedChart(svg, width, height) {
  const data = props.regions.filter(r => r.regionId !== -1 && r.topFeatureMeans);
  if (!data.length) {
    renderSizeChart(svg, width, height);
    return;
  }

  const features = Object.keys(data[0].topFeatureMeans);
  const legendRowH = Math.ceil(features.length / 4) * 20;
  const margin = { top: 18, right: 20, bottom: 44 + legendRowH, left: 54 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  const stackData = data.map(r => {
    const row = { region: `R${r.regionId}` };
    features.forEach(f => { row[f] = Math.abs(r.topFeatureMeans[f] || 0); });
    return row;
  });

  const stacked = d3.stack().keys(features)(stackData);
  const maxVal = d3.max(stacked[stacked.length - 1], d => d[1]);

  const x = d3.scaleBand().domain(stackData.map(d => d.region)).range([0, innerW]).padding(0.28);
  const y = d3.scaleLinear().domain([0, maxVal]).nice().range([innerH, 0]);
  const color = d3.scaleOrdinal(d3.schemePastel1).domain(features);

  g.append("g").attr("transform", `translate(0,${innerH})`)
    .call(d3.axisBottom(x))
    .call(ax => ax.selectAll("text").attr("fill", "#7d8ea0").attr("font-size", "11px"))
    .call(ax => ax.selectAll("line,path").attr("stroke", "#bcc9d5"));
  g.append("g")
    .call(d3.axisLeft(y).ticks(5))
    .call(ax => ax.selectAll("text").attr("fill", "#7d8ea0").attr("font-size", "11px"))
    .call(ax => ax.selectAll("line,path").attr("stroke", "#bcc9d5"));

  stacked.forEach(layer => {
    g.selectAll(null).data(layer).join("rect")
      .attr("x", d => x(d.data.region))
      .attr("y", d => y(d[1]))
      .attr("height", d => Math.max(0, y(d[0]) - y(d[1])))
      .attr("width", x.bandwidth())
      .attr("fill", color(layer.key))
      .attr("opacity", 0.9)
      .append("title").text(d => `${layer.key}: ${Number(d.data[layer.key]).toFixed(3)}`);
  });

  // legend
  const legendG = svg.append("g").attr("transform", `translate(${margin.left}, ${height - legendRowH + 4})`);
  const perRow = 4;
  const itemW = innerW / perRow;
  features.forEach((f, i) => {
    const row = Math.floor(i / perRow);
    const col = i % perRow;
    legendG.append("rect")
      .attr("x", col * itemW).attr("y", row * 18).attr("width", 10).attr("height", 10)
      .attr("fill", color(f)).attr("rx", 2);
    legendG.append("text")
      .attr("x", col * itemW + 14).attr("y", row * 18 + 9)
      .attr("fill", "#5a6b7a").attr("font-size", "10px")
      .text(f.length > 10 ? f.slice(0, 9) + "…" : f);
  });
}

watch(() => [props.regions, mode.value], render, { deep: true });
useResizeObserver(containerRef, render);
</script>
