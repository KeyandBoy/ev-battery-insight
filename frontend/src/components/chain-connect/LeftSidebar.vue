<template>
  <aside class="left-sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-toggle" @click="isCollapsed = !isCollapsed">
      <el-icon :size="16">
        <component :is="isCollapsed ? 'Expand' : 'Fold'" />
      </el-icon>
    </div>

    <div v-show="!isCollapsed" class="sidebar-content">
      <!-- 功能模块导航 -->
      <div class="module-section">
        <div class="section-title">功能模块</div>
        <el-menu
          :default-active="activeModule"
          class="sidebar-menu"
          @select="handleModuleSelect"
        >
          <el-menu-item index="social">
            <el-icon><Connection /></el-icon>
            <span>关系网络展示</span>
          </el-menu-item>
          <el-menu-item index="text">
            <el-icon><Document /></el-icon>
            <span>文本关系提取</span>
          </el-menu-item>
          <el-menu-item index="projects">
            <el-icon><FolderOpened /></el-icon>
            <span>我的项目</span>
          </el-menu-item>
        </el-menu>
      </div>

      <el-divider />

      <!-- 布局算法选择 -->
      <div class="module-section">
        <div class="section-title">布局算法</div>
        <el-radio-group v-model="graphStore.layoutType" class="layout-group" @change="handleLayoutChange">
          <el-radio-button value="force">
            <el-icon><Promotion /></el-icon> 力导向
          </el-radio-button>
          <el-radio-button value="circular">
            <el-icon><Refresh /></el-icon> 环形
          </el-radio-button>
          <el-radio-button value="grid">
            <el-icon><Grid /></el-icon> 网格
          </el-radio-button>
          <el-radio-button value="tree">
            <el-icon><SetUp /></el-icon> 层次
          </el-radio-button>
        </el-radio-group>
      </div>

      <el-divider />

      <!-- 布局参数配置 -->
      <div class="module-section">
        <div class="section-title">布局参数</div>
        <div class="config-panel">
          <!-- 力导向参数 -->
          <template v-if="graphStore.layoutType === 'force'">
            <div class="config-item">
              <span class="config-label">斥力强度</span>
              <el-slider
                v-model="forceConfig.repulsion"
                :min="100"
                :max="2000"
                :step="50"
                size="small"
                @change="updateForceConfig"
              />
            </div>
            <div class="config-item">
              <span class="config-label">引力系数</span>
              <el-slider
                v-model="forceConfig.gravity"
                :min="0"
                :max="1"
                :step="0.05"
                size="small"
                @change="updateForceConfig"
              />
            </div>
            <div class="config-item">
              <span class="config-label">边长</span>
              <el-slider
                v-model="forceConfig.edgeLength"
                :min="30"
                :max="400"
                :step="10"
                size="small"
                @change="updateForceConfig"
              />
            </div>
            <div class="config-item">
              <span class="config-label">摩擦系数</span>
              <el-slider
                v-model="forceConfig.friction"
                :min="0"
                :max="1"
                :step="0.05"
                size="small"
                @change="updateForceConfig"
              />
            </div>
          </template>
        </div>
      </div>

      <el-divider />

      <!-- 视觉编码配置 -->
      <div class="module-section">
        <div class="section-title">视觉配置</div>
        <div class="config-panel">
          <div class="config-item">
            <span class="config-label">节点大小</span>
            <el-slider
              v-model="graphStore.visualConfig.nodeSize"
              :min="10"
              :max="80"
              :step="2"
              size="small"
            />
          </div>
          <div class="config-item">
            <span class="config-label">按权重缩放</span>
            <el-switch v-model="graphStore.visualConfig.nodeSizeByValue" size="small" />
          </div>
          <div class="config-item">
            <span class="config-label">显示标签</span>
            <el-switch v-model="graphStore.visualConfig.labelShow" size="small" />
          </div>
          <div class="config-item">
            <span class="config-label">标签字号</span>
            <el-slider
              v-model="graphStore.visualConfig.labelFontSize"
              :min="8"
              :max="24"
              :step="1"
              size="small"
            />
          </div>
          <div class="config-item">
            <span class="config-label">边宽度</span>
            <el-slider
              v-model="graphStore.visualConfig.edgeWidth"
              :min="0.5"
              :max="6"
              :step="0.5"
              size="small"
            />
          </div>
          <div class="config-item">
            <span class="config-label">显示关系标签</span>
            <el-switch v-model="graphStore.visualConfig.edgeLabelShow" size="small" />
          </div>
          <div class="config-item">
            <span class="config-label">边曲度</span>
            <el-slider
              v-model="graphStore.visualConfig.edgeCurveness"
              :min="0"
              :max="0.5"
              :step="0.05"
              size="small"
            />
          </div>
          <div class="config-item">
            <span class="config-label">节点形状</span>
            <el-select v-model="graphStore.visualConfig.symbolType" size="small" style="width: 100%;">
              <el-option label="圆形" value="circle" />
              <el-option label="方形" value="rect" />
              <el-option label="菱形" value="diamond" />
              <el-option label="三角" value="triangle" />
              <el-option label="圆角方" value="roundRect" />
            </el-select>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useGraphStore } from '../../stores/chain-connect/graph'

const emit = defineEmits(['module-change'])
const graphStore = useGraphStore()
const isCollapsed = ref(false)
const activeModule = ref('social')

const forceConfig = reactive({
  ...graphStore.layoutConfig.force
})

// 同步 store 的 force 配置到本地（如加载项目时）
watch(() => graphStore.layoutConfig.force, (newVal) => {
  Object.assign(forceConfig, newVal)
}, { deep: true })

function handleModuleSelect(index) {
  activeModule.value = index
  emit('module-change', index)
  // 通过全局事件通知其他组件
  window.dispatchEvent(new CustomEvent('module-change', { detail: { module: index } }))
}

function handleLayoutChange(val) {
  graphStore.setLayoutType(val)
}

function updateForceConfig() {
  graphStore.updateLayoutConfig('force', { ...forceConfig })
}
</script>

<style scoped>
.left-sidebar {
  width: 280px;
  background: #fff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  position: relative;
  flex-shrink: 0;
  transition: width 0.3s ease;
  overflow: hidden;
}

.left-sidebar.collapsed {
  width: 40px;
}

.sidebar-toggle {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 4px;
  z-index: 10;
  color: #909399;
  transition: all 0.2s;
}

.sidebar-toggle:hover {
  background: #f5f7fa;
  color: #409EFF;
}

.sidebar-content {
  padding: 12px;
  overflow-y: auto;
  flex: 1;
}

.module-section {
  margin-bottom: 4px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
  padding-left: 4px;
}

.sidebar-menu {
  border-right: none !important;
}

:deep(.sidebar-menu .el-menu-item) {
  height: 40px;
  line-height: 40px;
  border-radius: 8px;
  margin-bottom: 4px;
  font-size: 14px;
}

:deep(.sidebar-menu .el-menu-item.is-active) {
  background: #ecf5ff;
  color: #409EFF;
}

.layout-group {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

:deep(.layout-group .el-radio-button__inner) {
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px !important;
  border: 1px solid #dcdfe6 !important;
}

.config-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-label {
  font-size: 12px;
  color: #606266;
  white-space: nowrap;
  min-width: 72px;
}

:deep(.el-divider) {
  margin: 12px 0;
}
</style>
