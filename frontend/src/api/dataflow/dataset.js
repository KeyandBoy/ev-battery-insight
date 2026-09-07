import http from "./http";

export async function uploadDataset(formData) {
  const response = await http.post("/datasets/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function fetchDatasets(page = 1, pageSize = 50) {
  const response = await http.get("/datasets", {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

export async function fetchDatasetPreview(datasetId, limit = 20) {
  const response = await http.get(`/datasets/${datasetId}/preview`, {
    params: { limit },
  });
  return response.data;
}

export async function deleteDatasetById(datasetId) {
  const response = await http.delete(`/datasets/${datasetId}`);
  return response.data;
}