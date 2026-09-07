import http from "./http";

export async function fetchDashboards(page = 1, pageSize = 50) {
  const response = await http.get("/dashboards", {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

export async function createDashboard(payload) {
  const response = await http.post("/dashboards", payload);
  return response.data;
}

export async function fetchDashboardDetail(dashboardId) {
  const response = await http.get(`/dashboards/${dashboardId}`);
  return response.data;
}

export async function updateDashboard(dashboardId, payload) {
  const response = await http.put(`/dashboards/${dashboardId}`, payload);
  return response.data;
}

export async function deleteDashboard(dashboardId) {
  const response = await http.delete(`/dashboards/${dashboardId}`);
  return response.data;
}

export async function saveDashboardLayout(dashboardId, payload) {
  const response = await http.put(`/dashboards/${dashboardId}/layout`, payload);
  return response.data;
}

export async function publishDashboard(dashboardId, isPublished) {
  const response = await http.put(`/dashboards/${dashboardId}/publish`, {
    is_published: isPublished ? 1 : 0,
  });
  return response.data;
}