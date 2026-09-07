import axios from "axios";
import { ElMessage } from "element-plus";
import router from "../../router";

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "/api/dataflow",
  timeout: 10000,
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const responseData = error?.response?.data || {};
    const statusCode = Number(error?.response?.status || 0);
    const jwtMessage = responseData.message || responseData.msg;

    if (statusCode === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      router.push("/login");
      ElMessage.error("登录已过期，请重新登录");
    } else {
      const message =
        jwtMessage ||
        error?.message ||
        "请求失败，请稍后重试。";
      ElMessage.error(message);
    }

    return Promise.reject(error);
  }
);

export default http;