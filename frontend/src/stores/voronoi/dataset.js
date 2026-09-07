import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as datasetApi from '../../api/voronoi/dataset'

export const useDatasetStore = defineStore('dataset', () => {
  const datasets = ref([])
  const pagination = ref({ total: 0, page: 1, per_page: 20, pages: 0 })
  const currentDataset = ref(null)
  const currentTreeData = ref(null)
  const loading = ref(false)

  async function fetchDatasets(params = {}) {
    loading.value = true
    try {
      const res = await datasetApi.getDatasets({
        page: pagination.value.page,
        per_page: pagination.value.per_page,
        ...params,
      })
      datasets.value = res.data.items
      pagination.value = {
        total: res.data.total,
        page: res.data.page,
        per_page: res.data.per_page,
        pages: res.data.pages,
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchDatasetData(id) {
    loading.value = true
    try {
      const res = await datasetApi.getDatasetData(id)
      currentDataset.value = res.data.dataset_info
      currentTreeData.value = res.data.tree_data
      return res.data
    } finally {
      loading.value = false
    }
  }

  async function uploadDataset(formData) {
    const res = await datasetApi.uploadDataset(formData)
    return res
  }

  async function removeDataset(id) {
    await datasetApi.deleteDataset(id)
    datasets.value = datasets.value.filter((d) => d.id !== id)
    pagination.value.total = Math.max(0, pagination.value.total - 1)
  }

  async function editDataset(id, data) {
    const res = await datasetApi.updateDataset(id, data)
    const idx = datasets.value.findIndex((d) => d.id === id)
    if (idx !== -1) datasets.value[idx] = res.data
    return res
  }

  function resetVisualization() {
    currentDataset.value = null
    currentTreeData.value = null
  }

  return {
    datasets, pagination, currentDataset, currentTreeData, loading,
    fetchDatasets, fetchDatasetData, uploadDataset, removeDataset, editDataset, resetVisualization,
  }
})