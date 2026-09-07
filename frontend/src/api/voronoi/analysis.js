import request from './request'

export function applyPcaWeight(datasetId) {
  return request.post(`/analysis/pca-weight/${datasetId}`)
}

export function clusterCsv(formData) {
  return request.post('/analysis/cluster', formData)
}

export function saveClusterResult(data) {
  return request.post('/analysis/cluster/save', data)
}
