<template>
  <div>
    <!-- 顶部操作栏 -->
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <h3>数据集管理</h3>
        <el-input v-model="searchText" placeholder="搜索数据集..." clearable style="width:240px"
                  :prefix-icon="Search" @clear="handleSearch" @keyup.enter="handleSearch" />
      </div>
      <div class="header-actions">
        <div class="view-toggle">
          <button class="view-toggle-btn" :class="{ active: viewMode === 'table' }" @click="viewMode = 'table'" title="表格视图">
            <el-icon><Grid /></el-icon>
          </button>
          <button class="view-toggle-btn" :class="{ active: viewMode === 'card' }" @click="viewMode = 'card'" title="卡片视图">
            <el-icon><Menu /></el-icon>
          </button>
        </div>
        <el-button type="primary" :icon="UploadFilled" @click="uploadDialogVisible = true">
          上传数据集
        </el-button>
      </div>
    </div>

    <!-- 卡片视图（可拖拽排序） -->
    <div v-if="viewMode === 'card'" class="dataset-card-grid" v-loading="datasetStore.loading">
      <div
        v-for="(row, idx) in datasetStore.datasets"
        :key="row.id"
        class="dataset-card"
        :class="{ dragging: dragCardIndex === idx, 'drag-over': dragOverCardIndex === idx }"
        draggable="true"
        @dragstart="onCardDragStart(idx, $event)"
        @dragover.prevent="onCardDragOver(idx)"
        @dragleave="onCardDragLeave"
        @drop="onCardDrop(idx)"
        @dragend="onCardDragEnd"
      >
        <div class="card-title">
          <span class="drag-handle">⠿</span>
          <span>{{ row.name }}</span>
        </div>
        <div class="card-meta">
          <div class="meta-item">
            <strong>{{ row.node_count || 0 }}</strong>
            节点数
          </div>
          <div class="meta-item">
            <strong>{{ row.max_depth || 0 }}</strong>
            深度
          </div>
          <div class="meta-item">
            <strong>{{ row.leaf_count || 0 }}</strong>
            叶节点
          </div>
          <div class="meta-item">
            <strong>{{ row.file_size_display || '-' }}</strong>
            文件大小
          </div>
        </div>
        <div class="card-actions">
          <el-button size="small" type="success" text @click="openPreviewDrawer(row)">详情</el-button>
          <el-button size="small" type="primary" text @click="$router.push(`/voronoi/visualization/${row.id}`)">可视化</el-button>
          <el-button size="small" type="warning" text @click="openEditDialog(row)">编辑</el-button>
          <el-button size="small" type="danger" text @click="handleDelete(row)">删除</el-button>
        </div>
      </div>
      <el-empty v-if="!datasetStore.loading && datasetStore.datasets.length === 0" description="暂无数据集" style="grid-column:1/-1" />
    </div>

    <!-- 表格视图 -->
    <el-card v-else shadow="never">
      <el-table :data="datasetStore.datasets" stripe v-loading="datasetStore.loading" style="width:100%">
        <el-table-column prop="name" label="名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="original_filename" label="文件名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="node_count" label="节点数" width="90" align="center" />
        <el-table-column prop="max_depth" label="深度" width="70" align="center" />
        <el-table-column prop="leaf_count" label="叶节点" width="90" align="center" />
        <el-table-column prop="file_size_display" label="大小" width="100" align="center" />
        <el-table-column prop="created_at" label="上传时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="success" @click="openPreviewDrawer(row)">详情</el-button>
            <el-button link type="primary" @click="$router.push(`/voronoi/visualization/${row.id}`)">可视化</el-button>
            <el-button link type="warning" @click="openEditDialog(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!datasetStore.loading && datasetStore.datasets.length === 0" description="暂无数据集" />
    </el-card>

    <!-- 分页 -->
    <div style="display:flex;justify-content:flex-end;margin-top:16px" v-if="datasetStore.pagination.total > 0">
      <el-pagination
        v-model:current-page="datasetStore.pagination.page"
        :page-size="datasetStore.pagination.per_page"
        :total="datasetStore.pagination.total"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传层次数据集" width="520px" @close="resetUploadForm">
      <el-form ref="uploadFormRef" :model="uploadForm" :rules="uploadRules" label-width="80px">
        <el-form-item label="数据集名" prop="name">
          <el-input v-model="uploadForm.name" placeholder="为数据集取一个名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="3" placeholder="描述（可选）" />
        </el-form-item>
        <el-form-item label="JSON文件" prop="file">
          <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept=".json"
                     :on-change="handleFileChange" :on-remove="handleFileRemove" drag>
            <el-icon style="font-size:40px;color:#c0c4cc"><UploadFilled /></el-icon>
            <div style="margin-top:8px;color:#606266">拖拽文件到此处或 <em>点击选择</em></div>
            <template #tip>
              <div style="color:#909399;font-size:12px;margin-top:4px">仅支持 .json 格式，文件大小不超过 16MB</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑数据集" width="460px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="previewDrawerVisible" title="数据集详情" size="560px" direction="rtl">
      <div v-if="previewData" class="preview-drawer-content">
        <!-- 基本信息 -->
        <div class="preview-info-grid">
          <div class="info-item">
            <span class="info-label">名称</span>
            <span class="info-value">{{ previewData.dataset?.name }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">文件名</span>
            <span class="info-value">{{ previewData.dataset?.original_filename }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">节点数</span>
            <span class="info-value">{{ previewData.dataset?.node_count }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">最大深度</span>
            <span class="info-value">{{ previewData.dataset?.max_depth }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">叶节点数</span>
            <span class="info-value">{{ previewData.dataset?.leaf_count }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">文件大小</span>
            <span class="info-value">{{ previewData.dataset?.file_size_display }}</span>
          </div>
          <div class="info-item" v-if="previewData.dataset?.description">
            <span class="info-label">描述</span>
            <span class="info-value">{{ previewData.dataset.description }}</span>
          </div>
        </div>

        <!-- 树结构预览 -->
        <el-divider content-position="left">树结构预览</el-divider>
        <div class="tree-preview" v-if="previewData.preview">
          <TreeNode :node="previewData.preview" :depth="0" />
        </div>

        <!-- 操作按钮 -->
        <div style="margin-top:20px;display:flex;gap:12px">
          <el-button type="primary" @click="openJsonViewer">查看原始 JSON</el-button>
          <el-button type="success" @click="goVisualize">打开可视化</el-button>
        </div>
      </div>
      <div v-else style="text-align:center;padding:40px">
        <el-icon class="is-loading" :size="32"><Loading /></el-icon>
        <p style="margin-top:12px;color:#909399">加载中...</p>
      </div>
    </el-drawer>

    <!-- JSON 查看器对话框 -->
    <el-dialog v-model="jsonViewerVisible" title="原始 JSON 数据" width="720px" top="5vh">
      <div class="json-viewer-toolbar">
        <el-button size="small" :icon="CopyDocument" @click="copyJson">复制</el-button>
        <el-button size="small" :icon="Download" @click="downloadJson">下载</el-button>
      </div>
      <div class="json-viewer-content" v-loading="jsonLoading">
        <pre v-if="jsonContent">{{ jsonContent }}</pre>
        <el-empty v-else-if="!jsonLoading" description="暂无数据" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, defineComponent, h } from 'vue'
import { useRouter } from 'vue-router'
import { useDatasetStore } from '../../stores/voronoi/dataset'
import { getDataset, getDatasetRaw, getDatasetPreview } from '../../api/voronoi/dataset'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, UploadFilled, CopyDocument, Download, Loading, Grid, Menu } from '@element-plus/icons-vue'

const router = useRouter()
const datasetStore = useDatasetStore()

const viewMode = ref('card')
const searchText = ref('')

const dragCardIndex = ref(null)
const dragOverCardIndex = ref(null)

function onCardDragStart(index, e) {
  dragCardIndex.value = index
  e.dataTransfer.effectAllowed = 'move'
}
function onCardDragOver(index) {
  dragOverCardIndex.value = index
}
function onCardDragLeave() {
  dragOverCardIndex.value = null
}
function onCardDrop(index) {
  if (dragCardIndex.value !== null && dragCardIndex.value !== index) {
    const arr = [...datasetStore.datasets]
    const [moved] = arr.splice(dragCardIndex.value, 1)
    arr.splice(index, 0, moved)
    datasetStore.datasets = arr
  }
  dragOverCardIndex.value = null
}
function onCardDragEnd() {
  dragCardIndex.value = null
  dragOverCardIndex.value = null
}
const uploadDialogVisible = ref(false)
const editDialogVisible = ref(false)
const previewDrawerVisible = ref(false)
const jsonViewerVisible = ref(false)
const uploading = ref(false)
const editLoading = ref(false)
const jsonLoading = ref(false)
const uploadFormRef = ref(null)
const editFormRef = ref(null)
const uploadRef = ref(null)

const previewData = ref(null)
const jsonContent = ref('')
const currentPreviewId = ref(null)

const uploadForm = reactive({ name: '', description: '', file: null })
const uploadRules = {
  name: [{ required: true, message: '请输入数据集名称', trigger: 'blur' }],
  file: [{ required: true, message: '请选择JSON文件', validator: (r, v, cb) => uploadForm.file ? cb() : cb(new Error('请选择JSON文件')) }],
}
const editForm = reactive({ id: null, name: '', description: '' })
const editRules = {
  name: [{ required: true, message: '名称不能为空', trigger: 'blur' }],
}

const TreeNode = defineComponent({
  name: 'TreeNode',
  props: {
    node: { type: Object, required: true },
    depth: { type: Number, default: 0 },
  },
  setup(props) {
    return () => {
      const node = props.node
      const indent = props.depth * 20
      const hasChildren = node.children && node.children.length > 0
      const icon = hasChildren ? '📁' : '📄'
      const weightInfo = node.value != null ? ` (${node.value})` : ''

      const children = []
      children.push(
        h('div', {
          class: 'tree-node-row',
          style: { paddingLeft: indent + 'px' },
        }, [
          h('span', { class: 'tree-node-icon' }, icon),
          h('span', { class: 'tree-node-name' }, node.name),
          weightInfo ? h('span', { class: 'tree-node-weight' }, weightInfo) : null,
        ])
      )
      if (hasChildren) {
        node.children.forEach((child) => {
          children.push(h(TreeNode, { node: child, depth: props.depth + 1 }))
        })
      }
      return h('div', null, children)
    }
  },
})

onMounted(() => { loadData() })

async function loadData() {
  datasetStore.pagination.page = 1
  await datasetStore.fetchDatasets({ search: searchText.value || undefined })
}

function handleSearch() { loadData() }
function handlePageChange(page) {
  datasetStore.pagination.page = page
  datasetStore.fetchDatasets({ search: searchText.value || undefined })
}

function handleFileChange(file) { uploadForm.file = file.raw }
function handleFileRemove() { uploadForm.file = null }

function resetUploadForm() {
  uploadForm.name = ''
  uploadForm.description = ''
  uploadForm.file = null
  uploadRef.value?.clearFiles()
}

async function handleUpload() {
  const valid = await uploadFormRef.value.validate().catch(() => false)
  if (!valid) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', uploadForm.file)
    fd.append('name', uploadForm.name)
    fd.append('description', uploadForm.description)
    await datasetStore.uploadDataset(fd)
    ElMessage.success('上传成功')
    uploadDialogVisible.value = false
    loadData()
  } catch (err) {
    ElMessage.error(err?.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

function openEditDialog(row) {
  editForm.id = row.id
  editForm.name = row.name
  editForm.description = row.description || ''
  editDialogVisible.value = true
}

async function handleEdit() {
  const valid = await editFormRef.value.validate().catch(() => false)
  if (!valid) return
  editLoading.value = true
  try {
    await datasetStore.editDataset(editForm.id, { name: editForm.name, description: editForm.description })
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    loadData()
  } catch (err) {
    ElMessage.error(err?.message || '更新失败')
  } finally {
    editLoading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除数据集「${row.name}」吗？`, '删除确认', { type: 'warning' })
  } catch {
    return
  }
  try {
    await datasetStore.removeDataset(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (err) {
    ElMessage.error(err?.message || '删除失败')
  }
}

async function openPreviewDrawer(row) {
  previewDrawerVisible.value = true
  previewData.value = null
  currentPreviewId.value = row.id
  try {
    const [detailRes, previewRes] = await Promise.all([
      getDataset(row.id),
      getDatasetPreview(row.id, 4),
    ])
    previewData.value = {
      dataset: detailRes.data,
      preview: previewRes.data?.preview || previewRes.data,
    }
  } catch (err) {
    ElMessage.error(err?.message || '加载详情失败')
    previewDrawerVisible.value = false
  }
}

async function openJsonViewer() {
  jsonViewerVisible.value = true
  jsonLoading.value = true
  jsonContent.value = ''
  try {
    const res = await getDatasetRaw(currentPreviewId.value)
    jsonContent.value = JSON.stringify(res.data, null, 2)
  } catch (err) {
    ElMessage.error(err?.message || '加载原始数据失败')
  } finally {
    jsonLoading.value = false
  }
}

function copyJson() {
  if (!jsonContent.value) return
  navigator.clipboard.writeText(jsonContent.value).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

function downloadJson() {
  if (!jsonContent.value) return
  const blob = new Blob([jsonContent.value], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `dataset_${currentPreviewId.value}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function goVisualize() {
  previewDrawerVisible.value = false
  router.push(`/voronoi/visualization/${currentPreviewId.value}`)
}

function formatDate(iso) {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>
