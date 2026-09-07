<template>
  <div class="scatter-container" ref="containerRef"></div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as d3 from 'd3'

const CLUSTER_COLORS = [
  '#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f',
  '#edc948', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ac',
  '#5fa2ce', '#fc7d0b', '#264653', '#2a9d8f', '#e76f51',
]

const props = defineProps({
  data: { type: Array, default: () => [] },
  width: { type: Number, default: 0 },
  height: { type: Number, default: 400 },
})

const containerRef = ref(null)
let zoomBehavior = null

onMounted(() => {
  if (props.data.length) nextTick(() => render())
})

onBeforeUnmount(() => {
  if (containerRef.value) d3.select(containerRef.value).selectAll('*').remove()
  zoomBehavior = null
})

watch(() => props.data, () => {
  if (props.data.length) nextTick(() => render())
})

function render() {
  const container = containerRef.value
  if (!container || !props.data.length) return

  d3.select(container).selectAll('*').remove()

  const margin = { top: 24, right: 24, bottom: 40, left: 48 }
  const w = (props.width || container.clientWidth || 500) - margin.left - margin.right
  const h = props.height - margin.top - margin.bottom
  if (w < 50 || h < 50) return

  const svg = d3.select(container)
    .append('svg')
    .attr('width', w + margin.left + margin.right)
    .attr('height', h + margin.top + margin.bottom)

  const outerG = svg.append('g')
  const g = outerG.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  zoomBehavior = d3.zoom()
    .scaleExtent([0.5, 10])
    .on('zoom', (event) => outerG.attr('transform', event.transform))
  svg.call(zoomBehavior)

  const validData = props.data.filter((d) => Number.isFinite(d.x) && Number.isFinite(d.y))
  if (!validData.length) return
  const xExtent = d3.extent(validData, (d) => d.x)
  const yExtent = d3.extent(validData, (d) => d.y)
  const xPad = (xExtent[1] - xExtent[0]) * 0.08 || 1
  const yPad = (yExtent[1] - yExtent[0]) * 0.08 || 1

  const xScale = d3.scaleLinear()
    .domain([xExtent[0] - xPad, xExtent[1] + xPad])
    .range([0, w])

  const yScale = d3.scaleLinear()
    .domain([yExtent[0] - yPad, yExtent[1] + yPad])
    .range([h, 0])

  g.append('g')
    .attr('transform', `translate(0,${h})`)
    .call(d3.axisBottom(xScale).ticks(6))
    .selectAll('text').style('font-size', '11px')

  g.append('g')
    .call(d3.axisLeft(yScale).ticks(6))
    .selectAll('text').style('font-size', '11px')

  g.append('text')
    .attr('x', w / 2).attr('y', h + 34)
    .attr('text-anchor', 'middle')
    .style('font-size', '12px').style('fill', '#6b7280')
    .text('Component 1')

  g.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('x', -h / 2).attr('y', -36)
    .attr('text-anchor', 'middle')
    .style('font-size', '12px').style('fill', '#6b7280')
    .text('Component 2')

  const tooltip = d3.select(container)
    .append('div')
    .style('position', 'absolute')
    .style('display', 'none')
    .style('padding', '6px 10px')
    .style('background', 'rgba(15,23,42,0.9)')
    .style('color', '#f1f5f9')
    .style('border-radius', '6px')
    .style('font-size', '12px')
    .style('pointer-events', 'none')
    .style('z-index', '50')

  const circles = g.selectAll('circle')
    .data(props.data)
    .join('circle')
    .attr('cx', (d) => xScale(d.x))
    .attr('cy', (d) => yScale(d.y))
    .attr('r', 0)
    .attr('fill', (d) => CLUSTER_COLORS[d.cluster % CLUSTER_COLORS.length])
    .attr('opacity', 0.8)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1)
    .style('cursor', 'grab')
    .on('mouseenter', function (event, d) {
      d3.select(this).attr('r', 7).attr('opacity', 1)
      tooltip.style('display', 'block')
        .html(`<b>${d.label ?? ''}</b><br>Cluster: ${d.cluster}`)
    })
    .on('mousemove', function (event) {
      const rect = container.getBoundingClientRect()
      tooltip
        .style('left', (event.clientX - rect.left + 12) + 'px')
        .style('top', (event.clientY - rect.top - 10) + 'px')
    })
    .on('mouseleave', function () {
      d3.select(this).attr('r', 5).attr('opacity', 0.8)
      tooltip.style('display', 'none')
    })
    .call(d3.drag()
      .on('start', function () { d3.select(this).raise().style('cursor', 'grabbing').attr('r', 7).attr('opacity', 1).attr('stroke-width', 2) })
      .on('drag', function (event) { d3.select(this).attr('cx', event.x).attr('cy', event.y) })
      .on('end', function () { d3.select(this).style('cursor', 'grab').attr('r', 5).attr('opacity', 0.8).attr('stroke-width', 1) })
    )

  circles.transition().duration(500).delay((d, i) => i * 15)
    .attr('r', 5)

  const clusters = [...new Set(props.data.map((d) => d.cluster))].sort((a, b) => a - b)
  const legendG = svg.append('g').attr('transform', `translate(${margin.left + w - clusters.length * 80}, 8)`)

  clusters.forEach((cl, i) => {
    const lg = legendG.append('g').attr('transform', `translate(${i * 80}, 0)`)
    lg.append('circle').attr('r', 4).attr('fill', CLUSTER_COLORS[cl % CLUSTER_COLORS.length])
    lg.append('text').attr('x', 8).attr('y', 4).text(`Cluster ${cl}`)
      .style('font-size', '11px').style('fill', '#374151')
  })
}

function resetZoom() {
  const svgEl = containerRef.value?.querySelector('svg')
  if (svgEl && zoomBehavior) {
    d3.select(svgEl).transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity)
  }
}

defineExpose({ resetZoom })
</script>

<style scoped>
.scatter-container {
  position: relative;
  width: 100%;
}
</style>
