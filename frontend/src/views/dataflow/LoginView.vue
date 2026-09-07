<script setup>
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { useAuthStore } from "../../stores/dataflow/auth";

const router = useRouter();
const authStore = useAuthStore();
const activeTab = ref("login");
const loading = ref(false);

const loginForm = reactive({
  username: "",
  password: "",
});

const registerForm = reactive({
  username: "",
  password: "",
  email: "",
});

async function handleLogin() {
  loading.value = true;
  try {
    await authStore.login(loginForm);
    ElMessage.success("登录成功");
    await router.push("/dataflow");
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loading.value = false;
  }
}

async function handleRegister() {
  loading.value = true;
  try {
    await authStore.register(registerForm);
    ElMessage.success("注册成功，请使用新账号登录");
    activeTab.value = "login";
    loginForm.username = registerForm.username;
    loginForm.password = registerForm.password;
  } catch (error) {
    ElMessage.error(error.message);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <section class="login-intro">
      <div class="thesis-chip">毕业设计课题</div>
      <h1>基于正方化算法的层次数据可视化构件系统</h1>
      <p class="subtitle">
        面向层次数据的全流程平台，覆盖数据导入清洗、Treemap 智能布局、低代码大屏编辑与展示发布。
      </p>

      <div class="intro-card-list">
        <article class="intro-card intro-card-active">
          <h3>研究目标</h3>
          <p>解决复杂层次数据在传统图表中表达能力不足的问题，提升结构表达清晰度与业务洞察效率。</p>
        </article>
        <article class="intro-card">
          <h3>核心算法</h3>
          <p>采用 Squarified Treemap 正方化布局算法，使节点矩形比例更均衡，提升可读性与视觉稳定性。</p>
        </article>
        <article class="intro-card">
          <h3>系统特色</h3>
          <p>前后端分离架构，支持低代码拖拽式大屏配置，便于快速构建数据展示页面并持续扩展。</p>
        </article>
      </div>

      <div class="intro-gallery">
        <figure class="intro-gallery-item">
          <img src="/images/intro-architecture.svg" alt="系统架构图示" />
          <figcaption>系统架构总览</figcaption>
        </figure>
        <figure class="intro-gallery-item">
          <img src="/images/intro-treemap.svg" alt="Treemap图示" />
          <figcaption>Treemap 正方化布局</figcaption>
        </figure>
        <figure class="intro-gallery-item">
          <img src="/images/intro-editor.svg" alt="大屏图示" />
          <figcaption>可视化大屏编辑器</figcaption>
        </figure>
      </div>
    </section>

    <section class="login-panel">
      <el-card shadow="never" class="auth-card">
        <template #header>
          <div class="auth-title">欢迎进入系统</div>
        </template>

        <el-tabs v-model="activeTab" stretch class="auth-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form :model="loginForm" label-position="top" class="auth-form">
              <el-form-item label="用户名">
                <el-input v-model="loginForm.username" placeholder="请输入用户名" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  show-password
                  placeholder="请输入密码"
                />
              </el-form-item>
              <el-button type="primary" :loading="loading" class="auth-btn" @click="handleLogin">
                登录系统
              </el-button>
              <div class="auth-note">默认体验账号：admin / 123456</div>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form :model="registerForm" label-position="top" class="auth-form">
              <el-form-item label="用户名">
                <el-input v-model="registerForm.username" placeholder="3-50位用户名" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  show-password
                  placeholder="至少6位"
                />
              </el-form-item>
              <el-form-item label="邮箱（可选）">
                <el-input v-model="registerForm.email" placeholder="name@example.com" />
              </el-form-item>
              <el-button type="primary" :loading="loading" class="auth-btn" @click="handleRegister">
                创建账号
              </el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </section>
  </div>
</template>
