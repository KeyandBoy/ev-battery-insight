<template>
  <div class="view-stack">

    <!-- ── Section 1: Run History ───────────────────────────── -->
    <el-card class="glass-card" shadow="never">
      <div class="section-split">
        <div>
          <h3>运行历史</h3>
          <p>
            共 <strong>{{ workspace.runs.value.length }}</strong> 条记录。
            点击 <strong>查看结果</strong> 加载并跳转至控制台可视化；点击 <strong>加载</strong> 仅恢复参数到工作台。
          </p>
        </div>
        <el-space>
          <el-button
            type="success"
            plain
            :disabled="!workspace.currentRunId.value"
            @click="workspace.exportCurrentRun('json')"
          >导出 JSON</el-button>
          <el-button
            type="warning"
            plain
            :disabled="!workspace.currentRunId.value"
            @click="workspace.exportCurrentRun('csv')"
          >导出 CSV</el-button>
        </el-space>
      </div>

      <el-table
        :data="workspace.runs.value"
        height="360"
        :row-class-name="({ row }) => row.id === workspace.currentRunId.value ? 'is-selected-row' : ''"
        empty-text="暂无运行记录，请先在数据工作台执行分析。"
      >
        <el-table-column label="编号" width="80">
          <template #default="{ row }">
            <span style="font-weight:600;color:#2d78b5">#{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="datasetName" label="数据集" min-width="200" show-overflow-tooltip />
        <el-table-column prop="reducer" label="降维" width="90" />
        <el-table-column prop="algorithm" label="聚类" width="120" />
        <el-table-column label="保真分数" width="106">
          <template #default="{ row }">
            {{ Number(row.preservationScore || 0).toFixed(4) }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="158">
          <template #default="{ row }">{{ formatDate(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="176" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click.stop="loadAndView(row.id)">查看结果</el-button>
            <el-button size="small" plain @click.stop="workspace.loadRunDetail(row.id)">加载</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- ── Section 2: Comparison + Benchmark ─────────────────── -->
    <el-row :gutter="20">

      <!-- Run Comparison -->
      <el-col :xs="24" :xl="12">
        <el-card class="glass-card" shadow="never">
          <div class="section-split">
            <div>
              <h3>运行对比</h3>
              <p>选择两套方案，对比保真度、聚类质量与执行效率。</p>
            </div>
            <el-button
              type="primary"
              :disabled="!canCompare"
              @click="workspace.executeRunComparison"
            >开始对比</el-button>
          </div>

          <div class="compare-selectors">
            <label>
              左侧运行
              <el-select
                v-model="workspace.selectedCompareRunIds.value[0]"
                placeholder="请选择左侧运行"
                clearable
              >
                <el-option
                  v-for="run in workspace.runs.value"
                  :key="`left-${run.id}`"
                  :label="buildRunLabel(run)"
                  :value="run.id"
                />
              </el-select>
            </label>
            <label>
              右侧运行
              <el-select
                v-model="workspace.selectedCompareRunIds.value[1]"
                placeholder="请选择右侧运行"
                clearable
              >
                <el-option
                  v-for="run in workspace.runs.value"
                  :key="`right-${run.id}`"
                  :label="buildRunLabel(run)"
                  :value="run.id"
                />
              </el-select>
            </label>
          </div>

          <template v-if="comparisonRows.length">
            <el-divider style="margin:18px 0 14px" />
            <el-table :data="comparisonRows" size="small">
              <el-table-column prop="metric" label="指标" min-width="150" />
              <el-table-column prop="left" label="左侧" min-width="96" />
              <el-table-column prop="right" label="右侧" min-width="96" />
              <el-table-column label="差值" min-width="96">
                <template #default="{ row }">
                  <span :class="deltaClass(row.rawDelta)">{{ row.delta }}</span>
                </template>
              </el-table-column>
            </el-table>
          </template>
          <el-empty v-else description="选择两个运行后点击「开始对比」" :image-size="64" />
        </el-card>
      </el-col>

      <!-- Benchmark -->
      <el-col :xs="24" :xl="12">
        <el-card class="glass-card" shadow="never">
          <div class="section-split">
            <div>
              <h3>批量基准测试</h3>
              <p>批量运行多套降维与聚类组合，快速识别最快和最保真的方案。</p>
            </div>
            <el-space>
              <el-input-number
                v-model="workspace.benchmarkRepeats.value"
                :min="1"
                :max="6"
                style="width:72px"
              />
              <el-button
                type="primary"
                :loading="workspace.loading.benchmark"
                @click="workspace.executeBenchmark"
              >运行测试</el-button>
            </el-space>
          </div>

          <el-row :gutter="12" style="margin-bottom:4px">
            <el-col :span="12">
              <div class="kpi-card kpi-card--light kpi-card--teal">
                <span class="kpi-card__label">最快场景</span>
                <strong class="kpi-card__value">
                  {{ workspace.benchmarkResult.value?.summary?.fastestLabel || '—' }}
                </strong>
                <span class="kpi-card__desc">
                  {{ formatMs(workspace.benchmarkResult.value?.summary?.fastestElapsedMs) }}
                </span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="kpi-card kpi-card--light kpi-card--amber">
                <span class="kpi-card__label">最佳保真</span>
                <strong class="kpi-card__value">
                  {{ workspace.benchmarkResult.value?.summary?.bestQualityLabel || '—' }}
                </strong>
                <span class="kpi-card__desc">
                  {{ format(workspace.benchmarkResult.value?.summary?.bestQualityScore) }}
                </span>
              </div>
            </el-col>
          </el-row>

          <template v-if="workspace.benchmarkResult.value?.results?.length">
            <el-divider style="margin:18px 0 14px" />
            <el-table
              :data="workspace.benchmarkResult.value.results"
              size="small"
            >
              <el-table-column prop="label" label="场景" min-width="180" show-overflow-tooltip />
              <el-table-column label="平均耗时" width="106">
                <template #default="{ row }">{{ formatMs(row.aggregate.totalElapsedMsMean) }}</template>
              </el-table-column>
              <el-table-column label="平均保真" width="96">
                <template #default="{ row }">{{ format(row.aggregate.preservationScoreMean) }}</template>
              </el-table-column>
              <el-table-column label="平均轮廓" width="96">
                <template #default="{ row }">{{ format(row.aggregate.silhouetteMean) }}</template>
              </el-table-column>
              <el-table-column label="平均噪声" width="96">
                <template #default="{ row }">{{ format(row.aggregate.noiseRatioMean) }}</template>
              </el-table-column>
            </el-table>
          </template>
          <el-empty v-else description="点击「运行测试」开始基准测试" :image-size="64" />
        </el-card>
      </el-col>

    </el-row>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useWorkspace } from "../../composables/region/useWorkspace";

const router = useRouter();
const workspace = useWorkspace();

const canCompare = computed(
  () => !!(workspace.selectedCompareRunIds.value[0] && workspace.selectedCompareRunIds.value[1])
);

const comparisonRows = computed(() =>
  Object.entries(workspace.comparisonResult.value?.metrics || {}).map(([metric, item]) => {
    const d = item.delta;
    let deltaStr = "—";
    if (d !== null && d !== undefined) {
      const n = Number(d);
      deltaStr = (n > 0 ? "+" : "") + n.toFixed(4);
    }
    return {
      metric,
      left: format(item.left),
      right: format(item.right),
      delta: deltaStr,
      rawDelta: d,
    };
  })
);

async function loadAndView(runId) {
  await workspace.loadRunDetail(runId);
  router.push("/region/dashboard");
}

function buildRunLabel(run) {
  return `#${run.id} · ${run.datasetName || `数据集${run.datasetId}`} · ${run.reducer} · ${run.algorithm}`;
}

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return (
    `${d.getFullYear()}-` +
    `${String(d.getMonth() + 1).padStart(2, "0")}-` +
    `${String(d.getDate()).padStart(2, "0")} ` +
    `${String(d.getHours()).padStart(2, "0")}:` +
    `${String(d.getMinutes()).padStart(2, "0")}`
  );
}

function deltaClass(raw) {
  if (raw === null || raw === undefined) return "";
  return Number(raw) > 0 ? "positive" : Number(raw) < 0 ? "negative" : "";
}

function format(value) {
  return value === null || value === undefined || Number.isNaN(Number(value))
    ? "—"
    : Number(value).toFixed(4);
}

function formatMs(value) {
  return value === null || value === undefined ? "—" : `${Number(value).toFixed(1)} ms`;
}
</script>
