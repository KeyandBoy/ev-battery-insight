<template>
  <div class="chart-container" ref="containerRef">
    <div class="chart-tooltip" ref="tooltipRef" style="display:none"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as d3 from 'd3'

const COLOR_SCHEMES = {
  classic: ['#4e79a7','#f28e2b','#e15759','#76b7b2','#59a14f','#edc948','#b07aa1','#ff9da7','#9c755f','#bab0ac'],
  ocean:   ['#264653','#2a9d8f','#e9c46a','#f4a261','#e76f51','#457b9d','#1d3557','#a8dadc','#168aad','#34a0a4'],
  forest:  ['#2d6a4f','#40916c','#52b788','#74c69d','#95d5b2','#1b4332','#344e41','#588157','#a3b18a','#3a5a40'],
  sunset:  ['#ff6b6b','#ee5a24','#ffa502','#ff6348','#ff7979','#f8a5c2','#786fa6','#cf6a87','#e77f67','#f19066'],
  tech:    ['#00b4d8','#0077b6','#48cae4','#023e8a','#03045e','#0096c7','#90e0ef','#5e60ce','#7400b8','#6930c3'],
}

const props = defineProps({
  data: { type: Object, default: null },
  colorScheme: { type: String, default: 'classic' },
  renderKey: { type: Number, default: 0 },
})

const containerRef = ref(null)
const tooltipRef = ref(null)
let simulation = null
let zoomBehavior = null

onMounted(() => { if (props.data) nextTick(() => render()) })
onBeforeUnmount(() => { destroy(); simulation?.stop() })

watch([() => props.data, () => props.renderKey, () => props.colorScheme], () => {
  if (props.data) nextTick(() => render())
}, { immediate: false })

function render() {
  const container = containerRef.value
  if (!container || !props.data) return
  destroy()
  simulation?.stop()

  const w = container.clientWidth, h = container.clientHeight
  if (w < 50 || h < 50) return

  const colors = COLOR_SCHEMES[props.colorScheme] || COLOR_SCHEMES.classic
  const root = d3.hierarchy(props.data)
  const nodes = root.descendants()
  const links = root.links()
  const topChildren = root.children || []

  const svg = d3.select(container).append('svg')
    .attr('width', w).attr('height', h)
    .attr('xmlns', 'http://www.w3.org/2000/svg')

  const g = svg.append('g')

  zoomBehavior = d3.zoom()
    .scaleExtent([0.3, 6])
    .on('zoom', (event) => g.attr('transform', event.transform))
  svg.call(zoomBehavior)

  simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(d => 60 - d.source.depth * 8).strength(0.8))
    .force('charge', d3.forceManyBody().strength(-120))
    .force('center', d3.forceCenter(w / 2, h / 2))
    .force('collision', d3.forceCollide().radius(d => nodeRadius(d) + 3))

  const link = g.selectAll('line')
    .data(links)
    .join('line')
    .attr('stroke', '#c0c4cc')
    .attr('stroke-width', d => Math.max(0.5, 2.5 - d.source.depth * 0.5))
    .attr('stroke-opacity', 0.6)

  const node = g.selectAll('circle')
    .data(nodes)
    .join('circle')
    .attr('r', d => nodeRadius(d))
    .attr('fill', d => {
      if (d.depth === 0) return '#667eea'
      const ancestor = d.ancestors().find(a => a.depth === 1) || d
      const idx = topChildren.indexOf(ancestor)
      const base = colors[(idx >= 0 ? idx : 0) % colors.length]
      const t = d.depth / (root.height || 1) * 0.4
      return d3.interpolateRgb(base, '#f0f5ff')(t)
    })
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .style('cursor', 'pointer')
    .on('mouseenter', (event, d) => showTooltip(event, d))
    .on('mousemove', (event) => moveTooltip(event))
    .on('mouseleave', () => hideTooltip())
    .call(d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x; d.fy = d.y
      })
      .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null; d.fy = null
      })
    )

  const label = g.selectAll('text')
    .data(nodes.filter(d => d.depth <= 2))
    .join('text')
    .attr('font-size', d => d.depth === 0 ? 13 : 10)
    .attr('fill', '#333')
    .attr('font-weight', d => d.depth <= 1 ? '600' : '400')
    .attr('text-anchor', 'middle')
    .attr('dy', d => nodeRadius(d) + 14)
    .attr('pointer-events', 'none')
    .text(d => { const n = d.data.name ?? ''; return n.length > 8 ? n.slice(0, 8) + '…' : n })

  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y)
    node.attr('cx', d => d.x).attr('cy', d => d.y)
    label.attr('x', d => d.x).attr('y', d => d.y)
  })
}

function nodeRadius(d) {
  if (d.depth === 0) return 12
  if (d.children) return Math.max(5, 10 - d.depth * 1.5)
  return 4
}

function escapeHtml(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML }

function showTooltip(event, d) {
  const tooltip = tooltipRef.value
  const lines = [`<b>${escapeHtml(d.data.name ?? '')}</b>`]
  if (d.data.value != null) lines.push(`权重: ${d.data.value}`)
  lines.push(`层级: ${d.depth}`)
  if (d.children?.length) lines.push(`子节点: ${d.children.length}`)
  else lines.push('叶节点')
  tooltip.innerHTML = lines.join('<br>')
  tooltip.style.display = 'block'
  moveTooltip(event)
}

function moveTooltip(event) {
  const rect = containerRef.value.getBoundingClientRect()
  let x = event.clientX - rect.left + 14, y = event.clientY - rect.top - 10
  if (x + 200 > rect.width) x -= 230
  tooltipRef.value.style.left = x + 'px'
  tooltipRef.value.style.top = y + 'px'
}

function hideTooltip() { tooltipRef.value.style.display = 'none' }

function getSvgElement() { return containerRef.value?.querySelector('svg') }
function destroy() { simulation?.stop(); if (containerRef.value) d3.select(containerRef.value).selectAll('svg').remove(); zoomBehavior = null }

function resetZoom() {
  const svgEl = containerRef.value?.querySelector('svg')
  if (svgEl && zoomBehavior) {
    d3.select(svgEl).transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity)
  }
}

defineExpose({ getSvgElement, resetZoom })
</script>
