import { defineStore } from "pinia";

import { fetchHealth } from "../../api/dataflow/health";

export const useAppStore = defineStore("app", {
  state: () => ({
    healthOk: false,
    healthText: "检测中...",
  }),
  actions: {
    async fetchHealthStatus() {
      try {
        const data = await fetchHealth();
        this.healthOk = data?.code === 0;
        this.healthText = this.healthOk ? "在线" : "异常";
      } catch (error) {
        this.healthOk = false;
        this.healthText = "离线";
      }
    },
  },
});