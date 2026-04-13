<template>
  <div class="version-history-page">
    <el-page-header @back="$router.back()">
      <template #content>
        <span class="page-title">版本历史</span>
      </template>
    </el-page-header>

    <el-card class="content-card" v-loading="loading">
      <!-- 图纸基本信息 -->
      <el-alert
        title="图纸信息"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #title>
          <div style="font-size: 13px">
            <strong>图号：</strong>{{ drawingInfo.drawing_no }}
            <strong style="margin-left: 20px">名称：</strong>{{ drawingInfo.name }}
            <strong style="margin-left: 20px">当前版本：</strong>
            <el-tag size="small" type="success">{{ currentVersion?.version_no || 'V1.0' }}</el-tag>
          </div>
        </template>
      </el-alert>

      <!-- 版本列表 -->
      <el-table :data="versions" stripe style="width: 100%">
        <el-table-column prop="version_no" label="版本号" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_latest ? 'success' : 'info'">
              {{ row.version_no }}
            </el-tag>
            <span v-if="row.is_latest" style="margin-left: 5px; color: #67c23a; font-size: 12px">
              当前版本
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="file_name" label="文件名" min-width="150" />

        <el-table-column prop="file_size" label="文件大小" width="100">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>

        <el-table-column label="文件格式" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.file_format || '-' }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="变更类型" min-width="200">
          <template #default="{ row }">
            <div v-if="row.change_types">
              <el-tag
                v-for="type in parseChangeTypes(row.change_types)"
                :key="type"
                size="small"
                :type="getChangeTypeTag(type)"
                style="margin-right: 5px; margin-bottom: 2px"
              >
                {{ getChangeTypeLabel(type) }}
              </el-tag>
            </div>
            <span v-else style="color: #c0c4cc">首次上传</span>
          </template>
        </el-table-column>

        <el-table-column label="变更原因" min-width="220">
          <template #default="{ row }">
            <el-tooltip
              v-if="row.change_reason && row.change_reason.length > 30"
              :content="row.change_reason"
              placement="top"
              effect="light"
            >
              <span>{{ row.change_reason.substring(0, 30) }}...</span>
            </el-tooltip>
            <span v-else-if="row.change_reason">{{ row.change_reason }}</span>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>

        <el-table-column label="问题单号" width="130">
          <template #default="{ row }">
            <el-tag v-if="row.related_issue" size="small" type="warning">
              {{ row.related_issue }}
            </el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="uploader_name" label="上传人" width="100" />

        <el-table-column prop="uploaded_at" label="上传时间" width="160">
          <template #default="{ row }">
            {{ row.uploaded_at ? row.uploaded_at.replace('T', ' ').substring(0, 16) : '' }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleDownload(row)">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button link type="primary" @click="handlePreview(row)">
              预览
            </el-button>
            <el-button
              v-if="!row.is_latest"
              link
              type="warning"
              @click="handleCompare(row)"
            >
              与当前对比
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 变更详情说明 -->
      <el-alert
        title="变更类型说明"
        type="info"
        :closable="false"
        show-icon
        style="margin-top: 15px"
      >
        <template #title>
          <div style="font-size: 12px; color: #606266">
            <span style="margin-right: 20px"><el-tag size="small" type="success">优化设计</el-tag> 对图纸进行设计优化</span>
            <span style="margin-right: 20px"><el-tag size="small" type="warning">修复问题</el-tag> 修复之前发现的问题</span>
            <span style="margin-right: 20px"><el-tag size="small" type="info">适配供应商</el-tag> 适配新供应商或材料</span>
            <span style="margin-right: 20px"><el-tag size="small">成本降低</el-tag> 降低成本或简化工艺</span>
            <span><el-tag size="small" type="info">其他</el-tag> 其他变更原因</span>
          </div>
        </template>
      </el-alert>

      <!-- 预览对话框 -->
      <el-dialog
        v-model="previewDialogVisible"
        title="文件预览"
        width="800px"
        class="preview-dialog"
      >
        <div v-if="previewLoading" style="text-align: center; padding: 50px">
          <el-icon class="is-loading" style="font-size: 50px"><Loading /></el-icon>
          <div style="margin-top: 20px">正在加载预览...</div>
        </div>
        <div v-else-if="previewError" style="text-align: center; padding: 50px; color: #f56c6c">
          <el-icon style="font-size: 50px"><WarningFilled /></el-icon>
          <div style="margin-top: 20px">{{ previewError }}</div>
        </div>
        <div v-else-if="isPdfFile" class="pdf-preview-container">
          <canvas ref="pdfCanvas"></canvas>
        </div>
        <div v-else style="text-align: center; padding: 50px; color: #909399">
          <el-icon style="font-size: 50px"><Document /></el-icon>
          <div style="margin-top: 20px">
            <p>{{ previewFileName }}</p>
            <p style="font-size: 12px; margin-top: 10px">
              此文件格式不支持在线预览，请下载后查看。
            </p>
          </div>
        </div>
        <template #footer>
          <el-button @click="previewDialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="handleDownload(previewRow)">
            <el-icon><Download /></el-icon>
            下载文件
          </el-button>
        </template>
      </el-dialog>

      <!-- 版本对比对话框 -->
      <el-dialog
        v-model="compareDialogVisible"
        title="版本对比"
        width="600px"
      >
        <div class="compare-container">
          <div class="compare-header">
            <span class="version-tag old">{{ compareData.oldVersion }}</span>
            <span class="arrow">→</span>
            <span class="version-tag new">{{ compareData.newVersion }}</span>
          </div>

          <el-divider />

          <div class="compare-section">
            <h4>变更类型</h4>
            <div class="compare-row">
              <span class="old-label">{{ compareData.oldVersion }}:</span>
              <el-tag
                v-for="type in compareData.oldChangeTypes"
                :key="type"
                size="small"
                :type="getChangeTypeTag(type)"
                style="margin-right: 5px"
              >
                {{ getChangeTypeLabel(type) }}
              </el-tag>
              <span v-if="!compareData.oldChangeTypes?.length" style="color: #c0c4cc">无</span>
            </div>
            <div class="compare-row">
              <span class="new-label">{{ compareData.newVersion }}:</span>
              <el-tag
                v-for="type in compareData.newChangeTypes"
                :key="type"
                size="small"
                :type="getChangeTypeTag(type)"
                style="margin-right: 5px"
              >
                {{ getChangeTypeLabel(type) }}
              </el-tag>
              <span v-if="!compareData.newChangeTypes?.length" style="color: #c0c4cc">无</span>
            </div>
          </div>

          <div class="compare-section">
            <h4>变更原因</h4>
            <div class="compare-row">
              <span class="old-label">{{ compareData.oldVersion }}:</span>
              <span class="reason-text">{{ compareData.oldReason || '无' }}</span>
            </div>
            <div class="compare-row">
              <span class="new-label">{{ compareData.newVersion }}:</span>
              <span class="reason-text">{{ compareData.newReason || '无' }}</span>
            </div>
          </div>

          <div class="compare-section" v-if="compareData.oldIssue || compareData.newIssue">
            <h4>问题单号</h4>
            <div class="compare-row">
              <span class="old-label">{{ compareData.oldVersion }}:</span>
              <span>{{ compareData.oldIssue || '无' }}</span>
            </div>
            <div class="compare-row">
              <span class="new-label">{{ compareData.newVersion }}:</span>
              <span>{{ compareData.newIssue || '无' }}</span>
            </div>
          </div>
        </div>

        <template #footer>
          <el-button @click="compareDialogVisible = false">关闭</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Download, Loading, WarningFilled, Document } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { api } from '../utils/api'
import * as pdfjsLib from 'pdfjs-dist'

// Set worker source for PDF.js
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url).href

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const drawingInfo = ref({
  drawing_no: '',
  name: '',
  current_version: ''
})

const versions = ref([])
const currentVersion = ref(null)

const compareDialogVisible = ref(false)
const previewDialogVisible = ref(false)
const previewLoading = ref(false)
const previewError = ref('')
const previewRow = ref(null)
const previewFileName = ref('')
const isPdfFile = ref(false)
const pdfCanvas = ref(null)

// Preview state
const pdfDoc = ref(null)
const currentPage = ref(1)
const totalPages = ref(0)

const compareData = reactive({
  oldVersion: '',
  newVersion: '',
  oldTime: '',
  newTime: '',
  oldChangeTypes: [],
  newChangeTypes: [],
  oldReason: '',
  newReason: '',
  oldIssue: '',
  newIssue: ''
})

// 加载图纸信息和版本历史
const loadVersions = async () => {
  loading.value = true
  try {
    // 获取图纸信息
    const drawingRes = await api.drawings.get(route.params.id)
    drawingInfo.value = drawingRes.data

    // 获取版本历史
    const versionsRes = await api.drawings.getVersions(route.params.id)
    versions.value = versionsRes.data || []
    currentVersion.value = versions.value.find(v => v.is_latest) || versions.value[0]

    // 加载上传人信息
    const uploaderIds = [...new Set(versions.value.map(v => v.uploader_id))]
    const uploadersMap = {}
    for (const id of uploaderIds) {
      try {
        const userRes = await api.users.get(id)
        uploadersMap[id] = userRes.data?.name || userRes.data?.username || '未知'
      } catch (e) {
        uploadersMap[id] = '未知'
      }
    }
    versions.value.forEach(v => {
      v.uploader_name = uploadersMap[v.uploader_id] || '未知'
    })
  } catch (error) {
    console.error('加载版本历史失败:', error)
    ElMessage.error('加载版本历史失败：' + error.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadVersions()
})

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const parseChangeTypes = (changeTypes) => {
  if (!changeTypes) return []
  return changeTypes.split(',').filter(t => t.trim())
}

const getChangeTypeLabel = (type) => {
  const map = {
    optimize: '优化设计',
    fix: '修复问题',
    supplier: '适配供应商',
    cost: '成本降低',
    other: '其他'
  }
  return map[type] || type
}

const getChangeTypeTag = (type) => {
  const map = {
    optimize: 'success',
    fix: 'warning',
    supplier: 'info',
    cost: '',
    other: 'info'
  }
  return map[type] || 'info'
}

const handleDownload = async (row) => {
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessage.error('请先登录')
    return
  }

  try {
    ElMessage.success(`正在下载 ${row.version_no}...`)

    const baseUrl = `/api/drawings/${route.params.id}/download?version_id=${row.id}&t=${Date.now()}`
    const response = await fetch(baseUrl, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Cache-Control': 'no-cache'
      }
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || '下载失败')
    }

    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = `${drawingInfo.value.drawing_no}_${row.version_no}.${row.file_format || 'dwg'}`
    if (contentDisposition) {
      const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (match) {
        filename = match[1].replace(/['"]/g, '')
      }
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error(error.message || '下载失败')
  }
}

const handlePreview = async (row) => {
  previewRow.value = row
  previewError.value = ''
  isPdfFile.value = false
  previewDialogVisible.value = true
  previewLoading.value = true

  const token = localStorage.getItem('token')
  if (!token) {
    previewLoading.value = false
    previewError.value = '请先登录'
    return
  }

  const fileFormat = (row.file_format || '').toLowerCase()
  previewFileName.value = row.file_name || `图纸_${row.version_no}`

  // Check if it's a PDF file
  if (fileFormat === 'pdf') {
    isPdfFile.value = true
    try {
      const previewUrl = `/api/drawings/${route.params.id}/download?version_id=${row.id}&t=${Date.now()}`
      const response = await fetch(previewUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache'
        }
      })

      if (!response.ok) {
        throw new Error('文件加载失败')
      }

      const blob = await response.blob()
      const arrayBuffer = await blob.arrayBuffer()

      // Load PDF document
      const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer })
      pdfDoc.value = await loadingTask.promise
      totalPages.value = pdfDoc.value.numPages
      currentPage.value = 1

      // Render first page
      await renderPdfPage(1)
      previewLoading.value = false
    } catch (error) {
      console.error('PDF预览失败:', error)
      previewLoading.value = false
      previewError.value = 'PDF文件加载失败：' + error.message
      isPdfFile.value = false
    }
  } else {
    // Not a PDF - show message
    previewLoading.value = false
    isPdfFile.value = false
  }
}

const renderPdfPage = async (pageNum) => {
  if (!pdfDoc.value || !pdfCanvas.value) return

  try {
    const page = await pdfDoc.value.getPage(pageNum)
    const viewport = page.getViewport({ scale: 1.5 })

    const canvas = pdfCanvas.value
    const context = canvas.getContext('2d')

    canvas.height = viewport.height
    canvas.width = viewport.width

    await page.render({
      canvasContext: context,
      viewport: viewport
    }).promise
  } catch (error) {
    console.error('渲染PDF页面失败:', error)
  }
}

const handleCompare = (row) => {
  const current = versions.value.find(v => v.is_latest) || versions.value[0]
  compareData.oldVersion = row.version_no
  compareData.newVersion = current.version_no
  compareData.oldTime = row.uploaded_at ? row.uploaded_at.replace('T', ' ').substring(0, 16) : ''
  compareData.newTime = current.uploaded_at ? current.uploaded_at.replace('T', ' ').substring(0, 16) : ''
  compareData.oldChangeTypes = parseChangeTypes(row.change_types)
  compareData.newChangeTypes = parseChangeTypes(current.change_types)
  compareData.oldReason = row.change_reason || ''
  compareData.newReason = current.change_reason || ''
  compareData.oldIssue = row.related_issue || ''
  compareData.newIssue = current.related_issue || ''
  compareDialogVisible.value = true
}
</script>

<style scoped>
.version-history-page {
  padding: 0;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
}

.content-card {
  margin-top: 15px;
}

.compare-container {
  padding: 10px 0;
}

.compare-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-bottom: 10px;
}

.version-tag {
  padding: 5px 15px;
  border-radius: 4px;
  font-weight: bold;
}

.version-tag.old {
  background: #fef0f0;
  color: #f56c6c;
}

.version-tag.new {
  background: #f0f9eb;
  color: #67c23a;
}

.arrow {
  color: #909399;
  font-size: 20px;
}

.compare-section {
  margin-bottom: 20px;
}

.compare-section h4 {
  margin: 0 0 10px 0;
  color: #303133;
  font-size: 14px;
}

.compare-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.old-label {
  color: #f56c6c;
  min-width: 60px;
}

.new-label {
  color: #67c23a;
  min-width: 60px;
}

.reason-text {
  color: #606266;
  white-space: pre-wrap;
}
</style>
