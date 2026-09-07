import http from "./http";

export async function fetchHealth() {
  const response = await http.get("/health");
  return response.data;
}