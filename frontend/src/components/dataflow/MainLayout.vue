<script setup>
import { computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { useAppStore } from "../../stores/dataflow/app";
import { useAuthStore } from "../../stores/dataflow/auth";
import { resolveBackendUrl } from "../../utils/dataflow/url";

const router = useRouter();
const route = useRoute();
const appStore = useAppStore();
const authStore = useAuthStore();

const menuItems = [
  { path: "/home", label: "系统首页" },
  { path: "/datasets", label: "数据集管理" },
  { path: "/treemap", label: "Treemap分析" },
  { path: "/dashboard-editor", label: "大屏编辑器" },
];

const activePath = computed(() => {
  const matched = menuItems.find((item) => route.path.startsWith(item.path));
  return matched ? matched.path : "/home";
});

const displayName = computed(() => {
  if (!authStore.user) {
    return "";
  }
  return authStore.user.display_name || authStore.user.username;
});

const avatarUrl = computed(() => resolveBackendUrl(authStore.user?.avatar_url || ""));

function handleMenuSelect(path) {
  router.push(path);
}

async function goProfile() {
  await router.push("/profile");
}

async function handleLogout() {
  authStore.logout();
  await router.push("/login");
  ElMessage.success("已退出登录");
}

onMounted(() => {
  appStore.fetchHealthStatus();
});
</script>

<template>
  <el-container class="app-shell">
    <el-header class="app-header">
      <div class="app-header-left">
        <div class="app-brand">
          <img class="app-brand-logo" src="/images/logo-dfc.svg" alt="DataFlowCanvas Logo" />
          <div class="app-brand-text">
            <span class="app-brand-title">DataFlowCanvas</span>
            <small class="app-brand-sub">层次数据可视化平台</small>
          </div>
        </div>
        <el-menu
          :default-active="activePath"
          mode="horizontal"
          :ellipsis="false"
          class="app-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
            {{ item.label }}
          </el-menu-item>
        </el-menu>
      </div>

      <div class="app-header-right">
        <el-tag
          class="backend-status"
          :type="appStore.healthOk ? 'success' : 'danger'"
          effect="plain"
        >
          后端{{ appStore.healthText }}
        </el-tag>
        <el-dropdown>
          <span class="user-entry">
            <el-avatar :size="38" :src="avatarUrl">
              {{ displayName ? displayName.slice(0, 1) : "U" }}
            </el-avatar>
            <span class="user-entry-name">{{ displayName }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="goProfile">个人资料</el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-main class="app-main">
      <RouterView />
    </el-main>
  </el-container>
</template>
