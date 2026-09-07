import { defineStore } from "pinia";

import { fetchMe, loginUser, registerUser, updateProfile, uploadAvatar } from "../../api/dataflow/auth";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("token") || "",
    user: null,
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
  },
  actions: {
    setToken(token) {
      this.token = token || "";
      if (this.token) {
        localStorage.setItem("token", this.token);
      } else {
        localStorage.removeItem("token");
      }
    },
    async register(payload) {
      return registerUser(payload);
    },
    async login(payload) {
      const result = await loginUser(payload);
      const token = result?.data?.access_token || result?.data?.token || "";
      this.setToken(token);
      this.user = result?.data?.user || null;
      if (result?.data?.user) {
        localStorage.setItem("user", JSON.stringify(result.data.user));
      }
      return result;
    },
    async loadCurrentUser() {
      if (!this.token) {
        this.user = null;
        return null;
      }
      try {
        const result = await fetchMe();
        this.user = result?.data || null;
        return this.user;
      } catch (error) {
        console.error("加载用户信息失败:", error);
        return null;
      }
    },
    async saveProfile(payload) {
      const result = await updateProfile(payload);
      this.user = result?.data || this.user;
      return result;
    },
    async saveAvatar(file) {
      const result = await uploadAvatar(file);
      this.user = result?.data?.user || this.user;
      return result;
    },
    logout() {
      this.user = null;
      this.setToken("");
      localStorage.removeItem("user");
    },
  },
});