<template>
  <div class="voronoi-container" ref="containerRef">
    <div class="voronoi-breadcrumb" v-if="breadcrumb.length > 1">
      <template v-for="(item, idx) in breadcrumb" :key="item.id">
        <span v-if="idx > 0" class="separator">/</span>
        <span :class="{ current: idx === breadcrumb.length - 1 }" @click="drillTo(idx)">{{ item.name }}</span>
      </template>
    </div>
    <div class="voronoi-legend" v-if="legend.length > 0">
      <div v-for="item in legend" :key="item.name" class="legend-item">
        <span class="legend-dot" :style="{ background: item.color }"></span>
        <span>{{ item.name }}</span>
      </div>
    </div>
    <div class="voronoi-tooltip" ref="tooltipRef" style="display:none"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as d3 from 'd3'
import { computeVoronoiTreemap } from '../../utils/voronoi/layout'
import { polygonArea, polygonCentroid, polygonBounds } from '../../utils/voronoi/geometry'

const COLOR_SCHEMES = {
  classic: ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948', '#b07aa1', '#ff9da7', '#9c755f', '#bab0ac', '#5fa2ce', '#fc7d0b'],
  ocean:   ['#264653', '#2a9d8f', '#e9c46a', '#f4a261', '#e76f51', '#457b9d', '#1d3557', '#a8dadc', '#168aad', '#34a0a4'],
  forest:  ['#2d6a4f', '#40916c', '#52b788', '#74c69d', '#95d5b2', '#1b4332', '#344e41', '#588157', '#a3b18a', '#3a5a40'],
  sunset:  ['#ff6b6b', '#ee5a24', '#ffa502', '#ff6348', '#ff7979', '#f8a5c2', '#786fa6', '#cf6a87', '#e77f67', '#f19066'],
  tech:    ['#00b4d8', '#0077b6', '#48cae4', '#023e8a', '#03045e', '#0096c7', '#90e0ef', '#5e60ce', '#7400b8', '#6930c3'],
}

const props = defineProps({
  data: { type: Object, default: null },
  iterations: { type: Number, default: 60 },
  padding: { type: Number, default: 2.5 },
  renderKey: { type: Number, default: 0 },
  colorScheme: { type: String, default: 'classic' },
  searchQuery: { type: String, default: '' },
})

const emit = defineEmits(['cellClick', 'cellHover'])

const containerRef = ref(null)
const tooltipRef = ref(null)
const breadcrumb = ref([])
const legend = ref([])

let svg = null
let mainGroup = null
let zoomBehavior = null
let resizeObserver = null
let currentRoot = null
let lastRenderedSize = { w: 0, h: 0 }
let resizeTimer = null
let allCellData = []

function getColors() {
  return COLOR_SCHEMES[props.colorScheme] || COLOR_SCHEMES.classic
}

onMounted(() => {
  resizeObserver = new ResizeObserver(() => {
    if (!currentRoot) return
    const { clientWidth: w, clientHeight: h } = containerRef.value
    if (Math.abs(w - lastRenderedSize.w) < 2 && Math.abs(h - lastRenderedSize.h) < 2) return
    clearTimeout(resizeTimer)
    resizeTimer = setTimeout(() => render(currentRoot), 200)
  })
  resizeObserver.observe(containerRef.value)
})

onBeforeUnmount(() => {
  clearTimeout(resizeTimer)
  resizeObserver?.disconnect()
  destroy()
})

watch(
  [() => props.data, () => props.renderKey, () => props.colorScheme],
  ([newData]) => {
    const root = newData || currentRoot
    if (root) {
      if (newData && newData !== currentRoot) {
        currentRoot = newData
        breadcrumb.value = [{ id: newData.id, name: newData.name, node: newData }]
      }
      nextTick(() => render(currentRoot))
    }
  },
  { immediate: true },
)

watch(() => props.searchQuery, () => {
  applySearchHighlight()
})

function render(rootNode) {
  const container = containerRef.value
  if (!container || !rootNode) return
  const width = container.clientWidth
  const height = container.clientHeight
  if (width < 10 || height < 10) return

  destroy()
  lastRenderedSize = { w: width, h: height }

  const cells = computeVoronoiTreemap(rootNode, width, height, {
    iterations: props.iterations,
    padding: props.padding,
  })
  allCellData = cells

  buildLegend(rootNode)
  const colors = getColors()

  svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('xmlns', 'http://www.w3.org/2000/svg')

  mainGroup = svg.append('g')

  zoomBehavior = d3.zoom()
    .scaleExtent([0.5, 10])
    .on('zoom', (event) => mainGroup.attr('transform', event.transform))
  svg.call(zoomBehavior)

  const maxDepth = Math.max(...cells.map((c) => c.depth), 0)
  const sorted = [...cells].sort((a, b) => a.depth - b.depth)

  const groups = mainGroup.selectAll('g.cell')
    .data(sorted, (d) => d.id)
    .join('g')
    .attr('class', 'cell')
    .style('opacity', 0)

  groups.transition().duration(400).delay((d, i) => i * 3).style('opacity', 1)

  groups.append('path')
    .attr('d', (d) => toPath(d.polygon))
    .attr('fill', (d) => cellColor(d, maxDepth, rootNode, colors))
    .attr('stroke', (d) => d.isLeaf ? 'rgba(255,255,255,0.8)' : 'rgba(50,50,80,0.2)')
    .attr('stroke-width', (d) => d.isLeaf ? 1 : Math.max(0.5, 3 - d.depth * 0.6))
    .style('cursor', (d) => (d.data?.children?.length ? 'pointer' : 'default'))
    .style('transition', 'stroke 0.15s, stroke-width 0.15s, opacity 0.2s')
    .on('mouseenter', function (event, d) { onHover(event, d, this) })
    .on('mousemove', (event) => moveTooltip(event))
    .on('mouseleave', function () { onLeave(this) })
    .on('click', (event, d) => onClick(event, d))

  groups.each(function (d) {
    if (!d.polygon || d.polygon.length < 3) return
    const area = Math.abs(polygonArea(d.polygon))
    if (area < 600 || !d.name) return
    const c = polygonCentroid(d.polygon)
    const fontSize = Math.min(14, Math.max(9, Math.sqrt(area) / 5))
    d3.select(this).append('text')
      .attr('x', c[0]).attr('y', c[1])
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'central')
      .attr('font-size', fontSize)
      .attr('fill', d.isLeaf ? '#2c3e50' : '#1a1a2e')
      .attr('font-weight', d.depth <= 1 ? '600' : '400')
      .attr('pointer-events', 'none')
      .attr('opacity', 0.85)
      .text(truncateLabel(d.name, area))
  })

  applySearchHighlight()
}

function cellColor(cell, maxDepth, rootNode, colors) {
  const topChildren = rootNode.children || []
  const pathParts = cell.id.split('/')
  const topName = pathParts.length > 1 ? pathParts[1] : pathParts[0]

  let colorIndex = topChildren.findIndex((c) => c.name === topName)
  if (colorIndex < 0) {
    let h = 0
    for (let i = 0; i < topName.length; i++) h = topName.charCodeAt(i) + ((h << 5) - h)
    colorIndex = Math.abs(h) % colors.length
  }
  const base = colors[colorIndex % colors.length]

  if (cell.isLeaf) {
    const t = Math.min(cell.depth / Math.max(maxDepth, 1), 1) * 0.5
    return d3.interpolateRgb(base, '#f0f5ff')(t)
  }
  return d3.interpolateRgb(base, '#ffffff')(0.78)
}

function buildLegend(rootNode) {
  const colors = getColors()
  if (!rootNode.children) { legend.value = []; return }
  legend.value = rootNode.children.map((child, i) => ({
    name: child.name,
    color: colors[i % colors.length],
  }))
}

function applySearchHighlight() {
  if (!mainGroup) return
  const q = (props.searchQuery || '').trim().toLowerCase()

  mainGroup.selectAll('g.cell').each(function (d) {
    const path = d3.select(this).select('path')
    const matched = q && d.name && d.name.toLowerCase().includes(q)

    if (q) {
      if (matched) {
        path.attr('stroke', '#ff4500').attr('stroke-width', 3).style('opacity', 1)
        d3.select(this).raise()
      } else {
        path.style('opacity', 0.35)
      }
    } else {
      path.style('opacity', 1)
        .attr('stroke', d.isLeaf ? 'rgba(255,255,255,0.8)' : 'rgba(50,50,80,0.2)')
        .attr('stroke-width', d.isLeaf ? 1 : Math.max(0.5, 3 - d.depth * 0.6))
    }
  })
}

function escapeHtml(str) {
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
}

function onHover(event, d, el) {
  if (props.searchQuery && !d.name?.toLowerCase().includes(props.searchQuery.toLowerCase())) return
  d3.select(el)
    .attr('stroke', '#409eff')
    .attr('stroke-width', 2.5)

  const tooltip = tooltipRef.value
  const lines = [`<b>${escapeHtml(d.name)}</b>`]
  if (d.value != null) lines.push(`权重值: ${d.value}`)
  lines.push(`层级: ${d.depth}`)
  if (d.data?.leaf_count) lines.push(`叶节点: ${d.data.leaf_count}`)
  if (d.data?.children?.length) lines.push(`子节点: ${d.data.children.length}`)
  tooltip.innerHTML = lines.join('<br>')
  tooltip.style.display = 'block'
  moveTooltip(event)
  emit('cellHover', d)
}

function moveTooltip(event) {
  if (!containerRef.value || !tooltipRef.value) return
  const tooltip = tooltipRef.value
  const rect = containerRef.value.getBoundingClientRect()
  let x = event.clientX - rect.left + 14
  let y = event.clientY - rect.top - 10
  if (x + 220 > rect.width) x = event.clientX - rect.left - 230
  if (y + 100 > rect.height) y = event.clientY - rect.top - 100
  tooltip.style.left = x + 'px'
  tooltip.style.top = y + 'px'
}

function onLeave(el) {
  const d = d3.select(el).datum()
  const q = (props.searchQuery || '').trim().toLowerCase()
  if (q) {
    const matched = d.name && d.name.toLowerCase().includes(q)
    d3.select(el)
      .attr('stroke', matched ? '#ff4500' : 'rgba(50,50,80,0.2)')
      .attr('stroke-width', matched ? 3 : 1)
  } else {
    d3.select(el)
      .attr('stroke', d.isLeaf ? 'rgba(255,255,255,0.8)' : 'rgba(50,50,80,0.2)')
      .attr('stroke-width', d.isLeaf ? 1 : Math.max(0.5, 3 - d.depth * 0.6))
  }
  tooltipRef.value.style.display = 'none'
}

function onClick(event, d) {
  if (d.data?.children?.length) drillDown(d, event)
  emit('cellClick', d)
}

function drillDown(cellData, event) {
  const node = cellData.data
  const polygon = cellData.polygon
  if (!polygon || polygon.length < 3) { directDrill(node); return }

  const bounds = polygonBounds(polygon)
  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight

  const cellW = bounds.xMax - bounds.xMin
  const cellH = bounds.yMax - bounds.yMin
  if (cellW < 1 || cellH < 1) { directDrill(node); return }

  const scale = Math.min(width / cellW, height / cellH) * 0.9
  const cx = (bounds.xMin + bounds.xMax) / 2
  const cy = (bounds.yMin + bounds.yMax) / 2
  const tx = width / 2 - cx * scale
  const ty = height / 2 - cy * scale

  const transform = d3.zoomIdentity.translate(tx, ty).scale(scale)

  mainGroup.selectAll('g.cell').select('path')
    .transition().duration(300)
    .style('opacity', (dd) => dd.id === cellData.id ? 1 : 0.15)

  svg.transition().duration(500)
    .call(zoomBehavior.transform, transform)
    .on('end', () => {
      currentRoot = node
      breadcrumb.value.push({ id: node.id, name: node.name, node })
      render(node)
    })
}

function directDrill(node) {
  currentRoot = node
  breadcrumb.value.push({ id: node.id, name: node.name, node })
  render(node)
}

function drillTo(index) {
  if (index >= breadcrumb.value.length - 1) return
  breadcrumb.value = breadcrumb.value.slice(0, index + 1)
  currentRoot = breadcrumb.value[index].node

  if (mainGroup) {
    mainGroup.selectAll('g.cell')
      .transition().duration(200)
      .style('opacity', 0)
      .on('end', () => render(currentRoot))
  } else {
    render(currentRoot)
  }
}

function resetZoom() {
  if (svg && zoomBehavior) {
    svg.transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity)
  }
}

function getSvgElement() {
  return containerRef.value?.querySelector('svg') || null
}

function destroy() {
  if (containerRef.value) {
    d3.select(containerRef.value).selectAll('svg').remove()
  }
  svg = null
  mainGroup = null
  allCellData = []
}

function toPath(polygon) {
  if (!polygon || polygon.length < 3) return ''
  return 'M' + polygon.map((p) => p[0].toFixed(2) + ',' + p[1].toFixed(2)).join('L') + 'Z'
}

function truncateLabel(name, area) {
  const s = name ?? ''
  const maxLen = Math.max(2, Math.floor(Math.sqrt(area) / 11))
  return s.length > maxLen ? s.slice(0, maxLen) + '…' : s
}

defineExpose({ resetZoom, drillTo, getSvgElement })
</script>
