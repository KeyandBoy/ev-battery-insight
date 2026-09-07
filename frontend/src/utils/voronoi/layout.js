/**
 * Voronoi Treemap 递归布局算法
 *
 * 核心流程:
 *  1. 为当前节点的子节点在父多边形内生成种子点
 *  2. 利用 d3-delaunay 计算 Voronoi 剖分
 *  3. 用 Sutherland-Hodgman 将每个 Voronoi 单元裁剪到父多边形边界
 *  4. 加权 Lloyd 松弛迭代优化（使面积逼近目标权重比例）
 *  5. 递归地对每个子节点重复上述过程
 */

import { Delaunay } from 'd3'
import {
  polygonArea, polygonCentroid, clipPolygon,
  polygonBounds, generatePointsInPolygon,
  pointInPolygon, shrinkPolygon,
} from './geometry'

const DEFAULTS = {
  iterations: 60,
  padding: 2.5,
  minCellArea: 4,
  convergenceThreshold: 0.01,
}

/**
 * 计算完整的 Voronoi Treemap 布局
 * @param {Object} rootData  - 预处理后的树形数据（含 normalized_value, id, depth, children）
 * @param {number} width     - 画布宽度
 * @param {number} height    - 画布高度
 * @param {Object} options   - 可选参数
 * @returns {Array} cells    - 所有单元格数组，每项含 { id, name, depth, polygon, isLeaf, data, ... }
 */
export function computeVoronoiTreemap(rootData, width, height, options = {}) {
  const opts = { ...DEFAULTS, ...options }
  const boundingPolygon = [
    [0, 0], [width, 0], [width, height], [0, height],
  ]
  const cells = []
  processNode(rootData, boundingPolygon, cells, 0, opts)
  return cells
}

function processNode(node, polygon, cells, depth, opts) {
  cells.push({
    id: node.id,
    name: node.name,
    value: node.value,
    normalizedValue: node.normalized_value,
    depth,
    polygon,
    isLeaf: !node.children || node.children.length === 0,
    data: node,
  })

  const children = node.children
  if (!children || children.length === 0) return

  const inner = shrinkPolygon(polygon, opts.padding)
  if (Math.abs(polygonArea(inner)) < opts.minCellArea) return

  if (children.length === 1) {
    processNode(children[0], inner, cells, depth + 1, opts)
    return
  }

  const weights = children.map((c) => c.normalized_value || 1 / children.length)
  const childPolygons = computeWeightedVoronoi(inner, weights, opts)

  for (let i = 0; i < children.length; i++) {
    const poly = childPolygons[i]
    if (poly && poly.length >= 3 && Math.abs(polygonArea(poly)) >= opts.minCellArea) {
      processNode(children[i], poly, cells, depth + 1, opts)
    }
  }
}

/**
 * 在 parentPolygon 内为 N 个子节点计算加权 Voronoi 剖分
 */
function computeWeightedVoronoi(parentPolygon, weights, opts) {
  const n = weights.length
  const totalArea = Math.abs(polygonArea(parentPolygon))
  const rawTotal = weights.reduce((a, b) => a + b, 0)
  const totalWeight = rawTotal > 0 ? rawTotal : n

  const seeds = generatePointsInPolygon(parentPolygon, n)
  let cells = new Array(n).fill(null)
  const bounds = polygonBounds(parentPolygon)
  const span = Math.max(bounds.xMax - bounds.xMin, bounds.yMax - bounds.yMin)
  const margin = span * 0.2

  const voronoiBounds = [
    bounds.xMin - margin, bounds.yMin - margin,
    bounds.xMax + margin, bounds.yMax + margin,
  ]

  for (let iter = 0; iter < opts.iterations; iter++) {
    const delaunay = Delaunay.from(seeds)
    const voronoi = delaunay.voronoi(voronoiBounds)

    for (let i = 0; i < n; i++) {
      const raw = voronoi.cellPolygon(i)
      if (!raw || raw.length < 4) { cells[i] = null; continue }
      const open = raw.slice(0, -1)
      const clipped = clipPolygon(open, parentPolygon)
      cells[i] = clipped.length >= 3 ? clipped : null
    }

    let maxShift = 0
    for (let i = 0; i < n; i++) {
      if (!cells[i] || cells[i].length < 3) continue

      const centroid = polygonCentroid(cells[i])
      const actualArea = Math.abs(polygonArea(cells[i]))
      const targetArea = totalArea * (weights[i] / totalWeight)
      if (actualArea < 1e-6) continue

      const ratio = targetArea / actualArea
      const adapt = Math.min(Math.max(Math.pow(ratio, 0.5), 0.25), 4.0)
      const decay = 1 - (iter / opts.iterations) * 0.3

      const nx = seeds[i][0] + (centroid[0] - seeds[i][0]) * adapt * decay
      const ny = seeds[i][1] + (centroid[1] - seeds[i][1]) * adapt * decay

      const shift = Math.hypot(nx - seeds[i][0], ny - seeds[i][1])
      if (shift > maxShift) maxShift = shift

      if (pointInPolygon([nx, ny], parentPolygon)) {
        seeds[i] = [nx, ny]
      } else if (pointInPolygon(centroid, parentPolygon)) {
        seeds[i] = centroid
      }
    }

    if (maxShift < opts.convergenceThreshold && iter > 10) break
  }

  return cells
}

export { DEFAULTS as layoutDefaults }
