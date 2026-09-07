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
let zoomBehavior = null

onMounted(() => { if (props.data) nextTick(() => render()) })
onBeforeUnmount(() => destroy())

watch([() => props.data, () => props.renderKey, () => props.colorScheme], () => {
  if (props.data) nextTick(() => render())
}, { immediate: false })

function render() {
  const container = containerRef.value
  if (!container || !props.data) return
  destroy()

  const w = container.clientWidth
  const h = container.clientHeight
  if (w < 50 || h < 50) return

  const radius = Math.min(w, h) / 2
  const colors = COLOR_SCHEMES[props.colorScheme] || COLOR_SCHEMES.classic

  const root = d3.hierarchy(props.data)
    .sum(d => d.children?.length ? 0 : (d.value || d.normalized_value || 1))
    .sort((a, b) => b.value - a.value)

  const partition = d3.partition().size([2 * Math.PI, radius])
  partition(root)

  const topChildren = root.children || []
  const colorScale = (d) => {
    const ancestor = d.ancestors().find(a => a.depth === 1) || d
    const idx = topChildren.indexOf(ancestor)
    const base = colors[(idx >= 0 ? idx : 0) % colors.length]
    const t = d.depth / (root.height || 1) * 0.5
    return d3.interpolateRgb(base, '#f0f5ff')(t)
  }

  const svg = d3.select(container).append('svg')
    .attr('width', w).attr('height', h)
    .attr('xmlns', 'http://www.w3.org/2000/svg')

  const g = svg.append('g')

  zoomBehavior = d3.zoom()
    .scaleExtent([0.3, 5])
    .on('zoom', (event) => g.attr('transform', event.transform))
  svg.call(zoomBehavior)
  svg.call(zoomBehavior.transform, d3.zoomIdentity.translate(w / 2, h / 2))

  const arc = d3.arc()
    .startAngle(d => d.x0)
    .endAngle(d => d.x1)
    .padAngle(0.005)
    .padRadius(radius / 2)
    .innerRadius(d => d.y0)
    .outerRadius(d => d.y1 - 1)

  g.selectAll('path')
    .data(root.descendants().filter(d => d.depth))
    .join('path')
    .attr('d', arc)
    .attr('fill', d => colorScale(d))
    .attr('stroke', '#fff')
    .attr('stroke-width', 0.5)
    .style('cursor', 'pointer')
    .style('opacity', 0)
    .on('mouseenter', (event, d) => showTooltip(event, d))
    .on('mousemove', (event) => moveTooltip(event))
    .on('mouseleave', () => hideTooltip())
    .transition().duration(600).delay((d, i) => i * 3)
    .style('opacity', 1)

  g.selectAll('text')
    .data(root.descendants().filter(d => d.depth && (d.x1 - d.x0) > 0.08))
    .join('text')
    .attr('transform', d => {
      const x = (d.x0 + d.x1) / 2 * 180 / Math.PI
      const y = (d.y0 + d.y1) / 2
      return `rotate(${x - 90}) translate(${y},0) rotate(${x < 180 ? 0 : 180})`
    })
    .attr('dy', '0.35em')
    .attr('text-anchor', 'middle')
    .attr('font-size', d => Math.min(11, (d.y1 - d.y0) * 0.3))
    .attr('fill', '#333')
    .attr('pointer-events', 'none')
    .text(d => {
      const name = d.data.name ?? ''
      const maxLen = Math.max(2, Math.floor((d.x1 - d.x0) * 10))
      return name.length > maxLen ? name.slice(0, maxLen) + '…' : name
    })
}

function escapeHtml(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML }

function showTooltip(event, d) {
  const tooltip = tooltipRef.value
  const lines = [`<b>${escapeHtml(d.data.name ?? '')}</b>`]
  if (d.value != null) lines.push(`权重: ${Number(d.value).toFixed(2)}`)
  lines.push(`层级: ${d.depth}`)
  if (d.children?.length) lines.push(`子节点: ${d.children.length}`)
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
function destroy() { if (containerRef.value) d3.select(containerRef.value).selectAll('svg').remove(); zoomBehavior = null }

function resetZoom() {
  const svgEl = containerRef.value?.querySelector('svg')
  if (svgEl && zoomBehavior) {
    const w = containerRef.value.clientWidth, h = containerRef.value.clientHeight
    d3.select(svgEl).transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity.translate(w / 2, h / 2))
  }
}

defineExpose({ getSvgElement, resetZoom })
</script>
