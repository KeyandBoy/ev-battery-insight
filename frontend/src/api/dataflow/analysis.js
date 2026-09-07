import http from "./http";

export async function fetchAnalysisFeatures(datasetId) {
  const response = await http.get("/analysis/features", {
    params: { dataset_id: datasetId },
  });
  return response.data;
}

export async function fetchTreemapLayout(datasetId, width, height, padding = 1, topN = 120, minRatio = 0.002) {
  const response = await http.get("/analysis/treemap", {
    params: {
      dataset_id: datasetId,
      width,
      height,
      padding,
      top_n: topN,
      min_ratio: minRatio,
    },
  });
  return response.data;
}

export async function fetchAnalysisPca(datasetId, maxRows = 300, maxFeatures = 6) {
  const response = await http.get("/analysis/pca", {
    params: {
      dataset_id: datasetId,
      max_rows: maxRows,
      max_features: maxFeatures,
    },
  });
  return response.data;
}