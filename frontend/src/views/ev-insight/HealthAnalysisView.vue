<template>
  <div class="ev-page">
    <div class="page-header">
      <div>
        <p class="eyebrow">EV-BATTERY INSIGHT</p>
        <h1>电池健康分析</h1>
        <p class="intro">上传标准化车辆电池数据，快速查看车辆健康分布与风险原因。</p>
      </div>
      <el-tag type="success" effect="dark">研究分析模式</el-tag>
    </div>

    <el-card class="upload-card" shadow="never">
      <template #header><span class="card-title">数据输入</span></template>
      <div class="upload-grid">
        <label class="file-box">
          <span>电池运行数据 <b>*</b></span>
          <small>需要包含 vehicle_id、temperature_c 等标准字段</small>
          <input type="file" accept=".csv" @change="readingsFile = $event.target.files[0]" />
          <strong>{{ readingsFile?.name || '选择 readings CSV' }}</strong>
        </label>
        <label class="file-box">
          <span>车辆信息数据</span>
          <small>可选，用于关联额定电池容量和车型信息</small>
          <input type="file" accept=".csv" @change="vehiclesFile = $event.target.files[0]" />
          <strong>{{ vehiclesFile?.name || '选择 vehicles CSV（可选）' }}</strong>
        </label>
      </div>
      <div class="actions">
        <el-button type="primary" size="large" :loading="loading" :disabled="!readingsFile" @click="analyze">开始分析</el-button>
        <span v-if="error" class="error">{{ error }}</span>
      </div>
    </el-card>

    <template v-if="summary">
      <div class="summary-grid">
        <el-card v-for="item in summaryCards" :key="item.label" class="metric-card" shadow="never">
          <small>{{ item.label }}</small>
          <strong :class="item.tone">{{ item.value }}</strong>
        </el-card>
      </div>

      <el-card class="result-card" shadow="never">
        <template #header><div class="result-header"><span class="card-title">车辆健康结果</span><span>共 {{ items.length }} 辆</span></div></template>
        <el-table :data="items" stripe height="480">
          <el-table-column prop="vehicle_id" label="车辆" min-width="120" />
          <el-table-column prop="health_score" label="健康分" width="100" sortable />
          <el-table-column prop="risk_level" label="风险等级" width="110">
            <template #default="scope"><el-tag :type="riskTag(scope.row.risk_level)">{{ scope.row.risk_level }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="mean_temperature_c" label="平均温度" width="110" />
          <el-table-column prop="max_temperature_c" label="最高温度" width="110" />
          <el-table-column prop="risk_reasons" label="主要原因" min-width="220" />
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { scoreBatteryHealth } from '@/api/ev-insight'

const readingsFile = ref(null)
const vehiclesFile = ref(null)
const loading = ref(false)
const error = ref('')
const summary = ref(null)
const items = ref([])

const summaryCards = computed(() => [
  { label: '分析车辆', value: summary.value.vehicleCount, tone: '' },
  { label: '平均健康分', value: summary.value.averageHealthScore, tone: 'blue' },
  { label: '关注车辆', value: summary.value.attentionCount, tone: 'orange' },
  { label: '高风险车辆', value: summary.value.highRiskCount, tone: 'red' }
])

async function analyze() {
  loading.value = true
  error.value = ''
  try {
    const response = await scoreBatteryHealth(readingsFile.value, vehiclesFile.value)
    summary.value = response.data.summary
    items.value = response.data.items
  } catch (requestError) {
    error.value = requestError.response?.data?.message || '分析失败，请确认服务已启动且 CSV 字段正确。'
  } finally {
    loading.value = false
  }
}

function riskTag(level) {
  return level === '高风险' ? 'danger' : level === '关注' ? 'warning' : level === '健康' ? 'success' : 'info'
}
</script>

<style scoped>
.ev-page { padding: 32px; max-width: 1400px; margin: 0 auto; }
.page-header, .result-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.eyebrow { color: #238a8d; font-size: 12px; letter-spacing: 0.16em; font-weight: 700; margin: 0 0 8px; }
h1 { margin: 0; color: #182b3a; font-size: 34px; }
.intro { color: #6b7d8c; margin: 10px 0 26px; }
.upload-card, .result-card, .metric-card { border: 1px solid #dfe9ed; border-radius: 14px; }
.card-title { color: #1d3445; font-weight: 700; }
.upload-grid, .summary-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.file-box { display: flex; flex-direction: column; gap: 7px; padding: 18px; border: 1px dashed #9ec7c8; border-radius: 12px; background: #f5fbfa; color: #1d3445; cursor: pointer; }
.file-box b { color: #d04a4a; }
.file-box small { color: #718493; }
.file-box input { display: none; }
.file-box strong { color: #238a8d; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.actions { display: flex; align-items: center; gap: 16px; margin-top: 20px; }
.error { color: #d04a4a; }
.summary-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 20px 0; }
.metric-card small { color: #718493; display: block; margin-bottom: 10px; }
.metric-card strong { color: #1d3445; font-size: 28px; }
.metric-card .blue { color: #2774a8; }.metric-card .orange { color: #c17b25; }.metric-card .red { color: #c44e4e; }
.result-header span:last-child { color: #718493; font-size: 13px; }
@media (max-width: 760px) { .ev-page { padding: 20px 14px; } h1 { font-size: 28px; } .upload-grid, .summary-grid { grid-template-columns: 1fr; } .page-header { flex-direction: column; } }
</style>
