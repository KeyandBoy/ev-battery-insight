import http from "./http";

export async function registerUser(payload) {
  const response = await http.post("/auth/register", payload);
  return response.data;
}

export async function loginUser(payload) {
  const response = await http.post("/auth/login", payload);
  return response.data;
}

export async function fetchMe() {
  const response = await http.get("/auth/me");
  return response.data;
}

export async function updateProfile(payload) {
  const response = await http.put("/auth/profile", payload);
  return response.data;
}

export async function updatePassword(payload) {
  const response = await http.put("/auth/password", payload);
  return response.data;
}

export async function uploadAvatar(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await http.post("/auth/avatar/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}