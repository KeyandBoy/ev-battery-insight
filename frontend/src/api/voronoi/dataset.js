import request from './request'

export function uploadDataset(formData) {
  return request.post('/datasets/upload', formData)
}

export function getDatasets(params) {
  return request.get('/datasets', { params })
}

export function getDataset(id) {
  return request.get(`/datasets/${id}`)
}

export function getDatasetData(id) {
  return request.get(`/datasets/${id}/data`)
}

export function getDatasetRaw(id) {
  return request.get(`/datasets/${id}/raw`)
}

export function getDatasetPreview(id, maxDepth = 3) {
  return request.get(`/datasets/${id}/preview`, { params: { max_depth: maxDepth } })
}

export function updateDataset(id, data) {
  return request.put(`/datasets/${id}`, data)
}

export function deleteDataset(id) {
  return request.delete(`/datasets/${id}`)
}
