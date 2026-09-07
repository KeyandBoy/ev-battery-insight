import axios from "axios";
import { ElMessage } from "element-plus";
import router from "../../router";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/region",
  timeout: 60000
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const responseData = error?.response?.data || {};
    const statusCode = Number(error?.response?.status || 0);

    if (statusCode === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      router.push("/login");
      ElMessage.error("登录已过期，请重新登录");
    } else {
      const message = responseData.message || error?.message || "请求失败";
      ElMessage.error(message);
    }

    return Promise.reject(error);
  }
);

export async function fetchDatasets() {
  const { data } = await client.get("/datasets");
  return data.items ?? [];
}

export async function fetchDatasetPreview(datasetId) {
  const { data } = await client.get(`/datasets/${datasetId}/preview`);
  return data;
}

export async function fetchDatasetSummary(datasetId) {
  const { data } = await client.get(`/datasets/${datasetId}/summary`);
  return data;
}

export async function generateDataset(datasetType) {
  const { data } = await client.post("/datasets/generate", { datasetType });
  return data.dataset;
}

export async function uploadDataset(formData) {
  const { data } = await client.post("/datasets/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data.dataset;
}

export async function deleteDataset(datasetId) {
  const { data } = await client.delete(`/datasets/${datasetId}`);
  return data;
}

export async function runAnalysis(payload) {
  const { data } = await client.post("/analysis/run", payload);
  return data;
}

export async function runBenchmark(payload) {
  const { data } = await client.post("/analysis/benchmark", payload);
  return data;
}

export async function fetchRuns() {
  const { data } = await client.get("/analysis/runs");
  return data.items ?? [];
}

export async function fetchRunDetail(runId) {
  const { data } = await client.get(`/analysis/runs/${runId}`);
  return data.run;
}

export async function compareRuns(runIds) {
  const { data } = await client.post("/analysis/compare", { runIds });
  return data;
}

export function getRunExportUrl(runId, format = "json") {
  return `${client.defaults.baseURL}/analysis/runs/${runId}/export?format=${format}`;
}