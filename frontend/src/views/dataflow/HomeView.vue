<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";

import { useAuthStore } from "../../stores/dataflow/auth";

const router = useRouter();
const authStore = useAuthStore();

const displayName = computed(() => {
  if (!authStore.user) {
    return "";
  }
  return authStore.user.display_name || authStore.user.username;
});

const modules = [
  {
    title: "数据集管理",
    desc: "上传 CSV / Excel / JSON，执行清洗并完成结构化入库。",
    path: "/dataflow/datasets",
  },
  {
    title: "Treemap分析",
    desc: "自动识别层级关系，提取特征并生成正方化布局坐标。",
    path: "/dataflow/treemap",
  },
  {
    title: "大屏编辑器",
    desc: "通过组件拖拽、属性配置和数据绑定快速构建可视化大屏。",
    path: "/dataflow/dashboard-editor",
  },
  {
    title: "个人资料",
    desc: "维护头像、昵称、邮箱和个人简介，支持本地图片上传。",
    path: "/dataflow/profile",
  },
];

const requirements = [
  "支持层次数据导入、预处理与结构识别",
  "实现基于正方化算法的 Treemap 可视化",
  "提供低代码拖拽式可视化大屏编辑能力",
  "支持组件数据绑定、布局保存与发布管理",
  "具备用户认证、资料管理与基础安全防护",
];

const techRoutes = [
  "数据侧：多格式文件导入、字段映射与质量校验",
  "算法侧：Squarified Treemap 递归切分与布局优化",
  "应用侧：组件化低代码编排与大屏渲染发布",
];

const deliverables = [
  "一套可复用的层次数据可视化前后端工程模板",
  "可稳定运行的 Treemap 分析流程与结果展示能力",
  "支持用户、数据集、分析结果与大屏配置管理的业务闭环",
];
</script>

<template>
  <div class="page-wrap home-page">
    <el-card shadow="never" class="home-hero">
      <div class="home-hero-title">欢迎回来，{{ displayName }}</div>
      <p class="home-hero-desc">
        本系统是你的毕业设计实现平台，聚焦层次数据可视化流程，覆盖数据导入、分析、布局生成与大屏呈现。
      </p>
    </el-card>

    <el-row :gutter="16" class="home-overview">
      <el-col :xs="24" :lg="15">
        <el-card shadow="never" class="home-detail-card">
          <template #header>
            <div class="card-header-title">项目说明</div>
          </template>
          <h3 class="home-detail-title">课题名称：基于正方化算法的层次数据可视化构件系统</h3>
          <p class="home-detail-text">
            系统面向文件系统、组织结构、产品分类等层次数据场景，采用 Flask + Vue3 前后端分离架构，
            通过 Squarified Treemap 算法提升复杂数据结构的可读性，并通过低代码编辑器提升可视化页面构建效率。
          </p>
          <p class="home-detail-text">
            项目聚焦“数据理解难、层级表达弱、可视构建慢”三类典型问题，强调从数据接入到可视发布的完整链路，
            让分析过程和展示结果能够在同一平台中持续迭代。
          </p>

          <div class="home-detail-block">
            <h4 class="home-detail-subtitle">功能需求覆盖</h4>
            <ul class="home-require-list">
              <li v-for="item in requirements" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div class="home-detail-block">
            <h4 class="home-detail-subtitle">技术路线</h4>
            <ul class="home-route-list">
              <li v-for="item in techRoutes" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div class="home-detail-block">
            <h4 class="home-detail-subtitle">预期交付成果</h4>
            <ul class="home-route-list">
              <li v-for="item in deliverables" :key="item">{{ item }}</li>
            </ul>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="9">
        <el-card shadow="never" class="home-detail-card">
          <template #header>
            <div class="card-header-title">系统主视觉</div>
          </template>
          <div class="home-hero-image-wrap">
            <img class="home-hero-image" src="/images/intro-showcase.svg" alt="DataFlowCanvas 系统展示图" />
            <p class="home-hero-image-note">
              从数据导入到 Treemap 分析，再到大屏发布的一体化流程主界面示意。
            </p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="home-process-card">
      <template #header>
        <div class="card-header-title">业务流程</div>
      </template>
      <el-steps :active="5" finish-status="success" align-center>
        <el-step title="数据导入" description="上传 CSV / Excel / JSON" />
        <el-step title="数据清洗" description="缺失值/重复值/异常处理" />
        <el-step title="结构分析" description="识别父子关系和层级深度" />
        <el-step title="Treemap布局" description="生成正方化可视坐标" />
        <el-step title="大屏发布" description="拖拽配置并保存展示页面" />
      </el-steps>
    </el-card>

    <el-divider content-position="left">系统模块入口</el-divider>

    <el-row :gutter="16" class="module-row">
      <el-col v-for="item in modules" :key="item.path" :xs="24" :sm="12" :md="12" :lg="6">
        <el-card shadow="hover" class="module-card module-card-plus">
          <h3>{{ item.title }}</h3>
          <p>{{ item.desc }}</p>
          <el-button type="primary" plain @click="router.push(item.path)">进入模块</el-button>
        </el-card>
      </el-col>
    </el-row>

    <footer class="home-footer">
      <span>© 2026 DataFlowCanvas</span>
      <span>毕业设计项目</span>
    </footer>
  </div>
</template>
