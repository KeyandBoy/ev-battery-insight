const API_BASE = '/api/dataflow'

export function resolveBackendUrl(path) {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  if (path.startsWith('/')) {
    return `${API_BASE}${path}`
  }
  return `${API_BASE}/${path}`
}