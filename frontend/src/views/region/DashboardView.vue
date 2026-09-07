<template>
  <div class="view-stack">

    <!-- ── Empty State ─────────────────────────────────────── -->
    <div v-if="!workspace.analysisResult.value" class="dashboard-empty">
      <div class="dashboard-empty__inner">
        <div class="dashboard-empty__icon">◎</div>
        <p class="dashboard-empty__eyebrow">尚无分析结果</p>
        <h2 class="dashboard-empty__title">选择数据集并运行分析</h2>
        <p class="dashboard-empty__desc">
          在数据工作台中选择或上传数据集、配置降维与聚类参数，点击「运行完整分析」后结果将在此展示。
          也可在实验中心点击「查看结果」加载历史运行。
        </p>
        <el-space wrap style="justify-content:center">
          <el-button type="primary" size="large" @click="router.push('/region')">
            前往数据工作台
          </el-button>
          <el-button size="large" plain @click="router.push('/region/experiment')">
            查看历史运行
          </el-button>
        </el-space>
      </div>
    </div>

    <!-- ── Results ─────────────────────────────────────────── -->
    <template v-else>

      <!-- Hero -->
      <section class="hero-panel">
        <div class="hero-panel__body">
          <p class="hero-panel__eyebrow">Analysis Console</p>
          <h2>高维数据区域分析控制台</h2>
          <p>
            通过区域划分、降维映射和质量评估，掌握数据集的整体结构、局部密度与模型保真表现。
          </p>
          <el-space wrap style="margin-top:18px">
            <el-button type="primary" @click="router.push('/region')">继续分析</el-button>
            <el-button type="success" plain @click="workspace.exportCurrentRun('json')">导出 JSON</el-button>
            <el-button type="warning" plain @click="workspace.exportCurrentRun('csv')">导出 CSV</el-button>
          </el-space>
        </div>
        <div class="hero-panel__stats">
          <div class="hero-stat">
            <span>当前数据集</span>
            <strong>{{ workspace.currentDataset.value?.name || workspace.analysisResult.value?.dataset?.name || '—' }}</strong>
          </div>
          <div class="hero-stat">
            <span>样本规模</span>
            <strong>{{ workspace.currentDataset.value?.sampleCount ?? workspace.analysisResult.value?.dataset?.sampleCount ?? 0 }}</strong>
          </div>
          <div class="hero-stat">
            <span>当前运行</span>
            <strong>{{ workspace.currentRunId.value ? `#${workspace.currentRunId.value}` : '—' }}</strong>
          </div>
          <div class="hero-stat">
            <span>区域数量</span>
            <strong>{{ workspace.visualization.value.regions?.length ?? 0 }}</strong>
          </div>
        </div>
      </section>

      <!-- KPI Cards -->
      <section class="dashboard-kpis">
        <el-card
          v-for="item in metricCards"
          :key="item.label"
          class="kpi-card"
          :class="`kpi-card--${item.accent}`"
          shadow="never"
        >
          <span class="kpi-card__label">{{ item.label }}</span>
          <strong class="kpi-card__value">{{ item.value }}</strong>
          <span class="kpi-card__desc">{{ item.description }}</span>
        </el-card>
      </section>

      <!-- Scatter + Region Summary -->
      <el-row :gutter="20">
        <el-col :xs="24" :xl="16">
          <el-card class="glass-card" shadow="never">
            <ScatterPlot
              :points="workspace.visualization.value.points"
              :polygons="workspace.visualization.value.voronoiPolygons"
              :regions="workspace.visualization.value.regions"
              :selected-region="workspace.selectedRegion.value"
              @select-region="workspace.setSelectedRegion"
            />
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="8">
          <el-card class="glass-card" shadow="never">
            <RegionSummary
              :regions="workspace.visualization.value.regions"
              :correlation="workspace.visualization.value.featureCorrelation"
              :selected-region="workspace.selectedRegion.value"
              @select-region="workspace.setSelectedRegion"
            />
          </el-card>
        </el-col>
      </el-row>

      <!-- Parallel Coordinates + Region Network -->
      <el-row :gutter="20">
        <el-col :xs="24" :xl="16">
          <el-card class="glass-card" shadow="never">
            <ParallelCoordinates
              :dimensions="workspace.visualization.value.parallelCoordinates.dimensions"
              :records="workspace.parallelRecords.value"
              :selected-region="workspace.selectedRegion.value"
            />
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="8">
          <el-card class="glass-card" shadow="never">
            <RegionNetwork
              :regions="workspace.visualization.value.regions"
              :links="workspace.visualization.value.regionLinks"
              :selected-region="workspace.selectedRegion.value"
              @select-region="workspace.setSelectedRegion"
            />
          </el-card>
        </el-col>
      </el-row>

      <!-- Feature Heatmap + Region Bar Chart -->
      <el-row :gutter="20">
        <el-col :xs="24" :xl="12">
          <el-card class="glass-card" shadow="never">
            <FeatureHeatmap :correlation="workspace.visualization.value.featureCorrelation" />
          </el-card>
        </el-col>
        <el-col :xs="24" :xl="12">
          <el-card class="glass-card" shadow="never">
            <RegionBarChart :regions="workspace.visualization.value.regions" />
          </el-card>
        </el-col>
      </el-row>

      <!-- Region Stats Table -->
      <el-card class="glass-card" shadow="never">
        <RegionStatsTable :regions="workspace.visualization.value.regions" />
      </el-card>

      <!-- Metrics Panel -->
      <el-card class="glass-card" shadow="never">
        <MetricsPanel
          :preprocess="workspace.analysisResult.value?.preprocess"
          :reduction="workspace.analysisResult.value?.reduction"
          :quality="workspace.analysisResult.value?.quality"
          :performance="workspace.analysisResult.value?.performance"
          :runs="workspace.runs.value"
          :current-run-id="workspace.currentRunId.value"
          @select-run="loadAndView"
        />
      </el-card>

    </template>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import MetricsPanel from "../../components/region/MetricsPanel.vue";
import ParallelCoordinates from "../../components/region/ParallelCoordinates.vue";
import RegionBarChart from "../../components/region/RegionBarChart.vue";
import RegionNetwork from "../../components/region/RegionNetwork.vue";
import RegionStatsTable from "../../components/region/RegionStatsTable.vue";
import RegionSummary from "../../components/region/RegionSummary.vue";
import ScatterPlot from "../../components/region/ScatterPlot.vue";
import FeatureHeatmap from "../../components/region/FeatureHeatmap.vue";
import { useWorkspace } from "../../composables/region/useWorkspace";

const router = useRouter();
const workspace = useWorkspace();

async function loadAndView(runId) {
  await workspace.loadRunDetail(runId);
  // Already on overview, just scroll to top
  window.scrollTo({ top: 0, behavior: "smooth" });
}

const metricCards = computed(() => {
  const preprocess = workspace.analysisResult.value?.preprocess || {};
  const quality = workspace.analysisResult.value?.quality || {};
  const performance = workspace.analysisResult.value?.performance || {};
  const reduction = workspace.analysisResult.value?.reduction || {};
  const clustering = workspace.analysisResult.value?.clustering || {};

  return [
    {
      label: "输出维度",
      value: preprocess.outputDimensions ?? "—",
      description: "预处理后参与分析的核心特征数量",
      accent: "blue",
    },
    {
      label: "保真分数",
      value: format(quality.preservationScore),
      description: "综合 trustworthiness 与距离保持度",
      accent: "amber",
    },
    {
      label: "轮廓系数",
      value: format(quality.silhouette),
      description: "聚类内聚性与分离性综合指标（越高越好）",
      accent: "teal",
    },
    {
      label: "总耗时",
      value: performance.totalElapsedMs
        ? `${Number(performance.totalElapsedMs).toFixed(1)} ms`
        : "—",
      description: `降维: ${reduction.method || "—"} · 聚类: ${clustering.method || clustering.algorithm || "—"}`,
      accent: "violet",
    },
  ];
});

function format(value) {
  return value === null || value === undefined ? "—" : Number(value).toFixed(4);
}
</script>
