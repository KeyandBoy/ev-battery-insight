/**
 * 计算几何工具库
 * 包含多边形面积、质心、点在多边形内判定、Sutherland-Hodgman 裁剪等
 */

export function polygonArea(polygon) {
  if (!polygon || polygon.length < 3) return 0
  let area = 0
  const n = polygon.length
  for (let i = 0, j = n - 1; i < n; j = i++) {
    area += polygon[j][0] * polygon[i][1]
    area -= polygon[i][0] * polygon[j][1]
  }
  return area / 2
}

export function polygonCentroid(polygon) {
  if (!polygon || polygon.length === 0) return [0, 0]
  if (polygon.length < 3) {
    const avgX = polygon.reduce((s, p) => s + p[0], 0) / polygon.length
    const avgY = polygon.reduce((s, p) => s + p[1], 0) / polygon.length
    return [avgX, avgY]
  }
  let cx = 0, cy = 0, area = 0
  const n = polygon.length
  for (let i = 0, j = n - 1; i < n; j = i++) {
    const cross = polygon[j][0] * polygon[i][1] - polygon[i][0] * polygon[j][1]
    cx += (polygon[j][0] + polygon[i][0]) * cross
    cy += (polygon[j][1] + polygon[i][1]) * cross
    area += cross
  }
  area /= 2
  if (Math.abs(area) < 1e-10) {
    const avgX = polygon.reduce((s, p) => s + p[0], 0) / n
    const avgY = polygon.reduce((s, p) => s + p[1], 0) / n
    return [avgX, avgY]
  }
  return [cx / (6 * area), cy / (6 * area)]
}

export function pointInPolygon(point, polygon) {
  const [x, y] = point
  let inside = false
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i]
    const [xj, yj] = polygon[j]
    const dy = yj - yi
    if (dy === 0) continue
    if (((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / dy + xi)) {
      inside = !inside
    }
  }
  return inside
}

function isLeft(point, edgeStart, edgeEnd) {
  return (edgeEnd[0] - edgeStart[0]) * (point[1] - edgeStart[1])
       - (edgeEnd[1] - edgeStart[1]) * (point[0] - edgeStart[0])
}

function lineIntersection(p1, p2, p3, p4) {
  const x1 = p1[0], y1 = p1[1], x2 = p2[0], y2 = p2[1]
  const x3 = p3[0], y3 = p3[1], x4 = p4[0], y4 = p4[1]
  const denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
  if (Math.abs(denom) < 1e-10) return [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2]
  const t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
  return [x1 + t * (x2 - x1), y1 + t * (y2 - y1)]
}

/**
 * Sutherland-Hodgman 多边形裁剪
 * 将 subject 多边形裁剪到 clip 多边形内部
 */
export function clipPolygon(subject, clip) {
  let output = subject.slice()

  for (let i = 0; i < clip.length; i++) {
    if (output.length === 0) return []
    const input = output.slice()
    output = []
    const edgeStart = clip[i]
    const edgeEnd = clip[(i + 1) % clip.length]

    for (let j = 0; j < input.length; j++) {
      const current = input[j]
      const previous = input[(j + input.length - 1) % input.length]
      const currInside = isLeft(current, edgeStart, edgeEnd) >= 0
      const prevInside = isLeft(previous, edgeStart, edgeEnd) >= 0

      if (currInside) {
        if (!prevInside) {
          output.push(lineIntersection(previous, current, edgeStart, edgeEnd))
        }
        output.push(current)
      } else if (prevInside) {
        output.push(lineIntersection(previous, current, edgeStart, edgeEnd))
      }
    }
  }
  return output
}

export function polygonBounds(polygon) {
  if (!polygon || polygon.length === 0) return { xMin: 0, yMin: 0, xMax: 0, yMax: 0 }
  let xMin = Infinity, yMin = Infinity, xMax = -Infinity, yMax = -Infinity
  for (const [x, y] of polygon) {
    if (x < xMin) xMin = x
    if (y < yMin) yMin = y
    if (x > xMax) xMax = x
    if (y > yMax) yMax = y
  }
  return { xMin, yMin, xMax, yMax }
}

/** 在多边形内部生成 n 个随机点 */
export function generatePointsInPolygon(polygon, n) {
  const bounds = polygonBounds(polygon)
  const points = []
  let attempts = 0
  while (points.length < n && attempts < n * 200) {
    const x = bounds.xMin + Math.random() * (bounds.xMax - bounds.xMin)
    const y = bounds.yMin + Math.random() * (bounds.yMax - bounds.yMin)
    if (pointInPolygon([x, y], polygon)) {
      points.push([x, y])
    }
    attempts++
  }
  const centroid = polygonCentroid(polygon)
  while (points.length < n) {
    const angle = (points.length / n) * Math.PI * 2
    const r = Math.min(bounds.xMax - bounds.xMin, bounds.yMax - bounds.yMin) * 0.1
    points.push([centroid[0] + r * Math.cos(angle), centroid[1] + r * Math.sin(angle)])
  }
  return points
}

/** 向内收缩多边形（用于层级间视觉间隔） */
export function shrinkPolygon(polygon, amount) {
  if (amount <= 0 || polygon.length < 3) return polygon
  const centroid = polygonCentroid(polygon)
  const area = Math.abs(polygonArea(polygon))
  if (area < 1) return polygon
  const factor = Math.max(0.6, 1 - amount / Math.sqrt(area))
  return polygon.map(([x, y]) => [
    centroid[0] + (x - centroid[0]) * factor,
    centroid[1] + (y - centroid[1]) * factor,
  ])
}
