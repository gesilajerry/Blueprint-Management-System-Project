<template>
  <div class="drawing-detail-page">
    <!-- 面包屑导航 -->
    <el-breadcrumb separator="/">
      <el-breadcrumb-item :to="{ path: '/drawings' }">图纸管理</el-breadcrumb-item>
      <el-breadcrumb-item>图纸详情</el-breadcrumb-item>
    </el-breadcrumb>

    <div class="page-content">
      <!-- 作废水印 -->
      <div v-if="drawing.status === 'archived'" class="archived-watermark">作废</div>
      <el-row :gutter="20" v-loading="loading">
        <!-- 左侧：基础信息 -->
        <el-col :span="16">
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <span>基础信息</span>
                <div>
                  <el-button type="success" size="small" @click="handlePrint">
                    <el-icon><Printer /></el-icon> 打印
                  </el-button>
                  <el-button type="primary" size="small" @click="handleEdit" v-if="userStore.canEditDrawing() && drawing.status !== 'archived'">编辑</el-button>
                </div>
              </div>
            </template>

            <el-form :model="drawing" label-width="120px" class="info-form">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="图号">
                    <el-input v-model="drawing.drawing_no" readonly />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="版本号">
                    <el-tag type="primary">{{ currentVersion.version_no || 'V1.0' }}</el-tag>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="图纸名称">
                <el-input v-model="drawing.name" />
              </el-form-item>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="所属产品/项目">
                    <el-select v-model="drawing.product_id" placeholder="请选择" style="width: 100%" :loading="productsLoading">
                      <el-option
                        v-for="p in products"
                        :key="p.id"
                        :label="p.name"
                        :value="p.id"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="所属项目组">
                    <el-input :model-value="drawing.project_group_name || '-'" readonly />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="项目负责人">
                    <el-input :model-value="drawing.project_manager || '-'" readonly />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="审定状态">
                    <el-tag :type="drawing.review_status === 'approved' ? 'success' : drawing.review_status === 'rejected' ? 'danger' : 'info'">
                      {{ reviewStatusLabel }}
                    </el-tag>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20">
                <el-col :span="12">
                  <el-form-item label="创建人">
                    <el-input :model-value="drawing.creator_name || creatorName" readonly />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="创建日期">
                    <el-input :model-value="createdDateTime" readonly />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20" v-if="drawing.is_core_part && drawing.core_part_keywords && drawing.core_part_keywords.length > 0">
                <el-col :span="24">
                  <el-form-item label="核心部件关键词">
                    <el-tag v-for="kw in drawing.core_part_keywords" :key="kw.id" style="margin-right: 8px; margin-bottom: 4px">
                      {{ kw.keyword }}
                    </el-tag>
                  </el-form-item>
                </el-col>
              </el-row>
            </el-form>
          </el-card>

          <!-- 技术参数 -->
          <el-card class="info-card" style="margin-top: 15px">
            <template #header>
              <span>技术参数</span>
            </template>

            <el-form :model="technical" label-width="100px">
              <el-form-item label="用途背景">
                <el-input
                  v-model="technical.purpose"
                  type="textarea"
                  :rows="2"
                  placeholder="用在哪个产品/项目，设计目的"
                  readonly
                />
              </el-form-item>

              <el-form-item label="关键材料">
                <el-input v-model="technical.material" placeholder="主要材料类型" readonly />
              </el-form-item>

              <el-form-item label="关键尺寸">
                <el-input v-model="technical.dimensions" placeholder="主要尺寸参数" readonly />
              </el-form-item>

              <el-form-item label="保密要点">
                <el-input
                  v-model="technical.secret_points"
                  type="textarea"
                  :rows="2"
                  placeholder="核心创新点、易被逆向的点（仅内部可见）"
                  readonly
                />
              </el-form-item>
            </el-form>

            <el-alert
              type="info"
              :closable="false"
              show-icon
              style="margin-top: 10px"
            >
              <template #title>
                以上字段均为可选，用于技术知识沉淀
              </template>
            </el-alert>
          </el-card>

          <!-- 审核历史 -->
          <el-card class="info-card" style="margin-top: 15px">
            <template #header>
              <span>审核历史</span>
            </template>

            <el-table :data="reviewHistory" stripe style="width: 100%" size="small">
              <el-table-column prop="old_level" label="原等级" width="100">
                <template #default="{ row }">
                  <el-tag size="small">{{ getLevelLabel(row.old_level) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="new_level" label="新等级" width="100">
                <template #default="{ row }">
                  <el-tag :type="getLevelTagType(row.new_level)" size="small">{{ getLevelLabel(row.new_level) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="reason" label="原因" min-width="150" />
              <el-table-column prop="reviewer_name" label="审核人" width="100" />
              <el-table-column prop="created_at" label="审核时间" width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
            </el-table>

            <el-empty v-if="reviewHistory.length === 0" description="暂无审核记录" />
          </el-card>
        </el-col>

        <!-- 右侧：保密信息和文件 -->
        <el-col :span="8">
          <!-- 保密等级 -->
          <el-card class="info-card">
            <template #header>
              <span>保密等级</span>
            </template>

            <div class="level-info">
              <el-tag :type="getLevelTagType(drawing.confidentiality_level)" size="large">
                {{ getLevelLabel(drawing.confidentiality_level) }}
              </el-tag>

              <el-descriptions :column="1" size="small" style="margin-top: 15px">
                <el-descriptions-item label="核心部件">
                  <el-tag :type="drawing.is_core_part ? 'danger' : 'info'" size="small">
                    {{ drawing.is_core_part ? '是' : '否' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="上传人">
                  {{ drawing.latest_version?.uploader_name || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="上传时间">
                  {{ drawing.latest_version?.uploaded_at ? drawing.latest_version.uploaded_at.replace('T', ' ').substring(0, 16) : '-' }}
                </el-descriptions-item>
              </el-descriptions>

              <el-button
                type="warning"
                size="small"
                style="width: 100%; margin-top: 10px"
                @click="handleLevelReview"
                v-if="userStore.hasPermission('reviewConfidentiality')"
              >
                <el-icon><Document /></el-icon>
                保密审核
              </el-button>
            </div>
          </el-card>

          <!-- 文件信息 -->
          <el-card class="info-card" style="margin-top: 15px">
            <template #header>
              <span>图纸文件</span>
            </template>

            <div class="file-info" v-if="drawing.latest_version?.file_name">
              <el-icon class="file-icon"><Document /></el-icon>
              <div class="file-meta">
                <div class="file-name">{{ drawing.latest_version.file_name }}</div>
                <div class="file-size">{{ formatFileSize(drawing.latest_version.file_size) }} · {{ drawing.latest_version.file_format }}</div>
              </div>
            </div>
            <div class="file-info" v-else>
              <el-icon class="file-icon"><Document /></el-icon>
              <div class="file-meta">
                <div class="file-name">暂无文件</div>
              </div>
            </div>

            <div class="file-actions">
              <el-button type="primary" @click="handlePreview" :disabled="!drawing.latest_version?.file_name">
                <el-icon><View /></el-icon>
                预览
              </el-button>
              <el-button type="success" @click="handleShowDownloadDialog" :disabled="!drawing.latest_version?.file_name">
                <el-icon><Download /></el-icon>
                下载
              </el-button>
            </div>

            <el-divider />

            <el-button
              type="success"
              style="width: 100%"
              @click="handleUploadVersion"
              v-if="userStore.canEditDrawing() && drawing.status !== 'archived'"
            >
              <el-icon><Upload /></el-icon>
              上传新版本
            </el-button>
          </el-card>

          <!-- 预览对话框 -->
          <el-dialog
            v-model="previewDialogVisible"
            title="文件预览"
            width="800px"
            class="preview-dialog"
          >
            <!-- 作废水印 -->
            <div v-if="drawing.status === 'archived'" class="archived-watermark-dialog">作废</div>
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
              <el-button type="primary" @click="handleShowDownloadDialog">
                <el-icon><Download /></el-icon>
                下载文件
              </el-button>
            </template>
          </el-dialog>

          <!-- 版本选择下载对话框 -->
          <el-dialog
            v-model="downloadDialogVisible"
            title="选择下载版本"
            width="500px"
          >
            <el-alert
              type="info"
              :closable="false"
              show-icon
              style="margin-bottom: 20px"
            >
              <template #title>
                请选择要下载的版本
              </template>
            </el-alert>

            <el-table
              :data="versions"
              stripe
              style="width: 100%"
              size="small"
              highlight-current-row
              @row-click="handleVersionRowClick"
              :current-row-key="selectedVersionId"
            >
              <el-table-column label="选择" width="60">
                <template #default="{ row }">
                  <el-radio
                    v-model="selectedVersionId"
                    :value="row.id"
                    size="small"
                  >&nbsp;</el-radio>
                </template>
              </el-table-column>
              <el-table-column prop="version_no" label="版本号" width="100">
                <template #default="{ row }">
                  <el-tag size="small" :type="row.is_latest ? 'success' : 'info'">
                    {{ row.version_no }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="file_name" label="文件名" min-width="150" />
              <el-table-column prop="uploaded_at" label="上传时间" width="150">
                <template #default="{ row }">
                  {{ formatDate(row.uploaded_at) }}
                </template>
              </el-table-column>
            </el-table>

            <template #footer>
              <el-button @click="downloadDialogVisible = false">取消</el-button>
              <el-button type="primary" @click="handleDownload" :loading="downloading">
                <el-icon><Download /></el-icon>
                确认下载
              </el-button>
            </template>
          </el-dialog>

          <!-- 版本历史快捷入口 -->
          <el-card class="info-card" style="margin-top: 15px">
            <template #header>
              <div class="card-header">
                <span>版本历史</span>
                <el-button link type="primary" @click="handleViewHistory">查看全部</el-button>
              </div>
            </template>

            <el-timeline style="padding-left: 10px">
              <el-timeline-item
                v-for="version in recentVersions"
                :key="version.id"
                :timestamp="formatDate(version.uploaded_at)"
                placement="top"
              >
                <el-tag size="small" :type="version.is_latest ? 'success' : 'info'">
                  {{ version.version_no }}
                </el-tag>
              </el-timeline-item>
              <el-timeline-item v-if="versions.length === 0">
                <span style="color: #909399">暂无版本记录</span>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑图纸信息"
      width="700px"
    >
      <el-form :model="editForm" :rules="editRules" ref="formRef" label-width="120px">
        <el-form-item label="图号">
          <el-input :value="drawing.drawing_no" readonly disabled />
          <div class="form-tip">图号生成后不可修改</div>
        </el-form-item>

        <el-form-item label="图纸名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入图纸名称" />
        </el-form-item>

        <el-form-item label="所属产品/项目" prop="product_id">
          <el-select v-model="editForm.product_id" placeholder="请选择" style="width: 100%" :loading="productsLoading">
            <el-option
              v-for="p in products"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="是否核心部件" prop="is_core_part">
          <el-checkbox v-model="editForm.is_core_part" label="涉及核心部件" border />
        </el-form-item>

        <el-form-item label="核心部件关键词" v-if="editForm.is_core_part">
          <el-checkbox-group v-model="editForm.core_part_keywords">
            <el-checkbox
              v-for="keyword in corePartKeywords"
              :key="keyword.id"
              :label="keyword.keyword"
              :value="keyword.id"
              border
            />
          </el-checkbox-group>
          <div class="form-tip">请选择与当前图纸相关的核心部件关键词</div>
        </el-form-item>

        <el-divider>技术参数</el-divider>

        <el-form-item label="用途背景">
          <el-input
            v-model="editForm.purpose"
            type="textarea"
            :rows="3"
            placeholder="用在哪个产品/项目，设计目的"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="关键材料">
          <el-input v-model="editForm.material" placeholder="如：铝合金 6061、不锈钢 304" maxlength="200" />
        </el-form-item>

        <el-form-item label="关键尺寸">
          <el-input v-model="editForm.dimensions" placeholder="如：500×300×200mm" maxlength="200" />
        </el-form-item>

        <el-form-item label="保密要点">
          <el-input
            v-model="editForm.secret_points"
            type="textarea"
            :rows="3"
            placeholder="核心创新点、易被逆向的点（仅内部可见）"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 审核对话框 -->
    <el-dialog
      v-model="reviewDialogVisible"
      title="保密审核"
      width="550px"
    >
      <el-form :model="reviewForm" label-width="120px">
        <el-form-item label="当前等级">
          <el-tag :type="getLevelTagType(drawing.confidentiality_level)" size="large">
            {{ getLevelLabel(drawing.confidentiality_level) }}
          </el-tag>
        </el-form-item>

        <el-form-item label="最终等级" required>
          <el-radio-group v-model="reviewForm.final_level">
            <el-radio value="A">A 类 - 核心机密</el-radio>
            <el-radio value="B">B 类 - 重要</el-radio>
            <el-radio value="C">C 类 - 一般</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="审核原因">
          <el-input
            v-model="reviewForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请填写审核原因"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="danger" @click="handleReject" :loading="submitting">驳回</el-button>
        <el-button type="primary" @click="handleApprove" :loading="submitting">通过</el-button>
      </template>
    </el-dialog>

    <!-- 打印对话框 -->
    <el-dialog
      v-model="printDialogVisible"
      title="打印预览"
      width="750px"
      :close-on-click-modal="false"
    >
      <!-- 作废水印 -->
      <div v-if="drawing.status === 'archived'" class="archived-watermark-dialog">作废</div>
      <div class="print-content" id="printArea">
        <div class="print-header">
          <h1>图纸信息表</h1>
          <p class="print-subtitle">图号：{{ drawing.drawing_no }} | 版本：{{ currentVersion.version_no || 'V1.0' }}</p>
          <p class="print-date">打印日期：{{ new Date().toLocaleDateString() }}</p>
        </div>

        <table class="print-table info-table">
          <colgroup>
            <col style="width: 15%">
            <col style="width: 35%">
            <col style="width: 15%">
            <col style="width: 35%">
          </colgroup>
          <tr>
            <th>图号</th>
            <td>{{ drawing.drawing_no }}</td>
            <th>图纸名称</th>
            <td>{{ drawing.name }}</td>
          </tr>
          <tr>
            <th>当前版本</th>
            <td>{{ currentVersion.version_no || 'V1.0' }}</td>
            <th>审核状态</th>
            <td>
              <span :class="['status-badge', 'status-' + drawing.review_status]">
                {{ getReviewStatusLabel(drawing.review_status) }}
              </span>
            </td>
          </tr>
          <tr>
            <th>保密等级</th>
            <td colspan="3">
              <span :class="['level-badge', 'level-' + drawing.confidentiality_level]">
                {{ getLevelLabel(drawing.confidentiality_level) }}
              </span>
            </td>
          </tr>
          <tr>
            <th>所属产品</th>
            <td>{{ drawing.product_name || '-' }}</td>
            <th>所属项目组</th>
            <td>{{ drawing.project_group_name || '-' }}</td>
          </tr>
          <tr>
            <th>创建人</th>
            <td>{{ drawing.creator_name || '-' }}</td>
            <th>创建时间</th>
            <td>{{ drawing.created_at ? drawing.created_at.substring(0, 10) : '-' }}</td>
          </tr>
          <tr v-if="drawing.is_core_part && drawing.core_part_keywords && drawing.core_part_keywords.length > 0">
            <th>核心部件关键词</th>
            <td colspan="3">
              <span v-for="kw in drawing.core_part_keywords" :key="kw.id" class="keyword-tag">{{ kw.keyword }}</span>
            </td>
          </tr>
          <tr>
            <th>用途背景</th>
            <td colspan="3">{{ technical.purpose || '-' }}</td>
          </tr>
          <tr>
            <th>关键材料</th>
            <td colspan="3">{{ technical.material || '-' }}</td>
          </tr>
          <tr>
            <th>关键尺寸</th>
            <td colspan="3">{{ technical.dimensions || '-' }}</td>
          </tr>
          <tr>
            <th>保密要点</th>
            <td colspan="3">{{ technical.secret_points || '-' }}</td>
          </tr>
        </table>

        <div class="print-section">
          <h3>版本变更历史</h3>
          <table class="print-table versions-table">
            <thead>
              <tr>
                <th>版本号</th>
                <th>文件名称</th>
                <th>变更类型</th>
                <th>变更原因</th>
                <th>上传人</th>
                <th>上传时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="v in versions" :key="v.id">
                <td>{{ v.version_no }}</td>
                <td>{{ v.file_name }}</td>
                <td>{{ getChangeTypeLabel(v.change_types) }}</td>
                <td>{{ v.change_reason || '-' }}</td>
                <td>{{ v.uploader_name || '-' }}</td>
                <td>{{ v.uploaded_at ? v.uploaded_at.substring(0, 10) : '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <template #footer>
        <el-button @click="printDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="doPrint">
          <el-icon><Printer /></el-icon> 打印
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Plus, Document, Download, Upload, View, Loading, WarningFilled, Printer
} from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../utils/api'
import * as pdfjsLib from 'pdfjs-dist'

// Set worker source for PDF.js
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL('pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url).href

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const productsLoading = ref(false)
const products = ref([])
const corePartKeywords = ref([])
const versions = ref([])
const creatorName = ref('')
const reviewHistory = ref([])

const drawing = reactive({
  id: '',
  drawing_no: '',
  name: '',
  product_id: '',
  project_group_id: '',
  project_group_name: '',
  project_manager: '',
  confidentiality_level: 'C',
  is_core_part: false,
  core_part_keywords: [],
  creator_id: '',
  creator_name: '',
  created_at: '',
  purpose: '',
  material: '',
  dimensions: '',
  secret_points: '',
  review_status: '',
  latest_version: null
})

const technical = reactive({
  purpose: '',
  material: '',
  dimensions: '',
  secret_points: ''
})

const currentVersion = ref({})
const recentVersions = ref([])

// 编辑相关
const editDialogVisible = ref(false)
const reviewDialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref(null)

// 预览相关
const previewDialogVisible = ref(false)
const previewLoading = ref(false)
const previewError = ref('')
const previewFileName = ref('')
const isPdfFile = ref(false)
const pdfCanvas = ref(null)
const pdfDoc = ref(null)

// 下载相关
const downloadDialogVisible = ref(false)
const selectedVersionId = ref('')
const downloading = ref(false)

// 打印相关
const printDialogVisible = ref(false)

const editForm = reactive({
  name: '',
  product_id: '',
  is_core_part: false,
  core_part_keywords: [],
  purpose: '',
  material: '',
  dimensions: '',
  secret_points: ''
})

const reviewForm = reactive({
  final_level: 'C',
  reason: ''
})

const editRules = {
  name: [{ required: true, message: '请输入图纸名称', trigger: 'blur' }],
  product_id: [{ required: true, message: '请选择产品/项目', trigger: 'change' }]
}

const createdDate = computed(() => {
  return drawing.created_at ? drawing.created_at.substring(0, 10) : ''
})

const createdDateTime = computed(() => {
  return drawing.created_at ? drawing.created_at.replace('T', ' ').substring(0, 16) : ''
})

const reviewStatusLabel = computed(() => {
  const map = { pending: '待审定', approved: '已通过', rejected: '已驳回' }
  return map[drawing.review_status] || '待审定'
})

// 加载产品列表
const loadProducts = async () => {
  productsLoading.value = true
  try {
    const res = await api.products.list({ page: 1, size: 100 })
    products.value = res.data?.items || []
  } catch (error) {
    console.error('加载产品列表失败:', error)
  } finally {
    productsLoading.value = false
  }
}

// 加载核心部件词库
const loadCorePartKeywords = async () => {
  try {
    const res = await api.coreParts.list({ page: 1, size: 100 })
    corePartKeywords.value = res.data?.items || []
  } catch (error) {
    console.error('加载核心部件词库失败:', error)
  }
}

// 加载审核历史
const loadReviewHistory = async () => {
  try {
    const res = await api.reviews.getHistory(route.params.id)
    reviewHistory.value = res.data || []
  } catch (error) {
    console.error('加载审核历史失败:', error)
  }
}

// 加载图纸详情
const loadDrawing = async () => {
  loading.value = true
  try {
    const res = await api.drawings.get(route.params.id)
    const data = res.data
    Object.assign(drawing, data)

    // 加载创建人信息
    if (data.creator_id) {
      try {
        const userRes = await api.users.get(data.creator_id)
        creatorName.value = userRes.data?.name || userRes.data?.username || '未知'
      } catch (e) {
        creatorName.value = '未知'
      }
    }

    // 加载技术参数
    technical.purpose = data.purpose || ''
    technical.material = data.material || ''
    technical.dimensions = data.dimensions || ''
    technical.secret_points = data.secret_points || ''

    // 加载版本历史
    const versionsRes = await api.drawings.getVersions(route.params.id)
    versions.value = versionsRes.data || []
    recentVersions.value = versions.value.slice(0, 3)
    currentVersion.value = versions.value.find(v => v.is_latest) || versions.value[0] || {}

    // 加载审核历史
    await loadReviewHistory()
  } catch (error) {
    console.error('加载图纸详情失败:', error)
    ElMessage.error('加载图纸详情失败：' + error.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadProducts()
  loadCorePartKeywords()
  loadDrawing()
})

const getLevelLabel = (level) => {
  const map = { A: 'A 类 - 核心机密', B: 'B 类 - 重要', C: 'C 类 - 一般' }
  return map[level] || level
}

const getLevelTagType = (level) => {
  const map = { A: 'danger', B: 'warning', C: 'info' }
  return map[level] || 'info'
}

const getChangeTypeLabel = (type) => {
  const map = {
    initial: '首次上传',
    fix: '修复问题',
    optimization: '优化设计',
    major_change: '重大变更',
    supplier: '适配供应商',
    cost: '成本降低',
    other: '其他'
  }
  return map[type] || type || '-'
}

const getReviewStatusLabel = (status) => {
  const map = {
    pending: '待审核',
    approved: '已审定',
    rejected: '已驳回'
  }
  return map[status] || status || '-'
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateStr) => {
  return dateStr ? dateStr.replace('T', ' ').substring(0, 16) : ''
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return ''
  // 如果包含T（ISO格式）
  if (dateStr.includes('T')) {
    return dateStr.replace('T', ' ').substring(0, 16)
  }
  // 如果是空格分隔的格式（2026-04-11 08:40:56.325218）
  if (dateStr.includes(' ')) {
    return dateStr.substring(0, 19)
  }
  return dateStr
}

const handleEdit = async () => {
  // 将当前数据复制到编辑表单
  editForm.product_id = drawing.product_id
  editForm.name = drawing.name
  editForm.is_core_part = drawing.is_core_part || false
  editForm.core_part_keywords = drawing.core_part_keywords?.map(k => k.id) || []
  editForm.purpose = technical.purpose
  editForm.material = technical.material
  editForm.dimensions = technical.dimensions
  editForm.secret_points = technical.secret_points
  editDialogVisible.value = true
}

const handleSave = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const params = {
          name: editForm.name,
          product_id: editForm.product_id,
          is_core_part: editForm.is_core_part,
          core_part_keywords: editForm.core_part_keywords.join(','),
          purpose: editForm.purpose || null,
          material: editForm.material || null,
          dimensions: editForm.dimensions || null,
          secret_points: editForm.secret_points || null
        }

        await api.drawings.update(route.params.id, params)
        ElMessage.success('保存成功')
        editDialogVisible.value = false
        loadDrawing()
      } catch (error) {
        console.error('保存失败:', error)
        ElMessage.error('保存失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleDownload = async () => {
  // 下载图纸文件
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessage.error('请先登录')
    return
  }

  downloading.value = true
  try {
    // 构建下载URL，包含选中的版本ID
    const baseUrl = `${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'}/drawings/${drawing.id}/download`
    const url = selectedVersionId.value
      ? `${baseUrl}?version_id=${selectedVersionId.value}&t=${Date.now()}`
      : `${baseUrl}?t=${Date.now()}`

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || '下载失败')
    }

    // 获取文件名：优先从 Content-Disposition header，失败则使用原始文件名
    const contentDisposition = response.headers.get('Content-Disposition')
    let filename = versions.value.find(v => v.id === selectedVersionId.value)?.file_name || `${drawing.drawing_no}.dwg`
    if (contentDisposition) {
      // 尝试从 header 中提取文件名
      const match = contentDisposition.match(/filename\*?[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (match) {
        filename = match[1].replace(/['"]/g, '')
        // 处理 URL 编码的文件名
        try {
          filename = decodeURIComponent(filename)
        } catch (e) {
          // 忽略解码错误
        }
      }
    }

    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)

    downloadDialogVisible.value = false
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error(error.message || '下载失败')
  } finally {
    downloading.value = false
  }
}

const handlePrint = () => {
  printDialogVisible.value = true
}

const doPrint = () => {
  const printContent = document.getElementById('printArea')
  if (!printContent) {
    ElMessage.error('打印内容加载失败')
    return
  }

  const newWindow = window.open('', '_blank')
  if (!newWindow) {
    ElMessage.error('请允许弹出窗口进行打印')
    return
  }

  newWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>图纸信息表 - ${drawing.drawing_no}</title>
      <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
          font-family: 'Microsoft YaHei', Arial, sans-serif;
          padding: 20px;
          font-size: 14px;
          color: #333;
        }
        .print-header {
          text-align: center;
          margin-bottom: 20px;
          border-bottom: 2px solid #409EFF;
          padding-bottom: 15px;
        }
        .print-header h1 {
          color: #409EFF;
          font-size: 24px;
          margin-bottom: 5px;
        }
        .print-subtitle {
          color: #409EFF;
          font-size: 14px;
          font-weight: bold;
          margin: 5px 0;
        }
        .print-date {
          color: #666;
          font-size: 12px;
        }
        .print-table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 20px;
        }
        .print-table th,
        .print-table td {
          border: 1px solid #ddd;
          padding: 10px 8px;
          text-align: left;
        }
        .print-table th {
          background: #f5f7fa;
          font-weight: 600;
          color: #606266;
        }
        .info-table th {
          width: 15%;
        }
        .info-table td {
          width: 35%;
        }
        .versions-table th,
        .versions-table td {
          text-align: center;
          font-size: 12px;
        }
        .versions-table th {
          background: #f5f7fa;
        }
        .print-section {
          margin-top: 25px;
        }
        .print-section h3 {
          font-size: 16px;
          color: #303133;
          margin-bottom: 10px;
          padding-left: 10px;
          border-left: 4px solid #409EFF;
        }
        /* 打印高亮样式 */
        .level-badge {
          padding: 4px 12px;
          border-radius: 4px;
          font-weight: bold;
          color: white;
        }
        .level-A { background: #F56C6C; }
        .level-B { background: #E6A23C; }
        .level-C { background: #909399; }
        .status-badge {
          padding: 4px 12px;
          border-radius: 4px;
          font-weight: bold;
          color: white;
        }
        .status-pending { background: #E6A23C; }
        .status-approved { background: #67C23A; }
        .status-rejected { background: #F56C6C; }
        .keyword-tag {
          display: inline-block;
          padding: 2px 8px;
          margin-right: 5px;
          background: #f0f9ff;
          border: 1px solid #91d5ff;
          border-radius: 4px;
          color: #1890ff;
          font-size: 12px;
        }
        @media print {
          body { padding: 0; }
        }
      </style>
    </head>
    <body>
      ${printContent.innerHTML}
    </body>
    </html>
  `)
  newWindow.document.close()
  newWindow.print()
  newWindow.close()
}

const handleShowDownloadDialog = () => {
  // 默认选中最新版本（第一项，因为列表已按上传时间倒序排列）
  if (versions.value.length > 0) {
    selectedVersionId.value = versions.value[0].id
  }
  downloadDialogVisible.value = true
}

const handleVersionRowClick = (row) => {
  selectedVersionId.value = row.id
}

const handleUploadVersion = () => {
  router.push(`/drawings/${route.params.id}/upload`)
}

const handlePreview = async () => {
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

  const fileFormat = (drawing.latest_version?.file_format || '').toLowerCase()
  previewFileName.value = drawing.latest_version?.file_name || `图纸_${drawing.latest_version?.version_no || 'V1.0'}`

  // Check if it's a PDF file
  if (fileFormat === 'pdf') {
    isPdfFile.value = true
    try {
      const response = await fetch(`${api.drawings.download(drawing.id)}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
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

const handleViewHistory = () => {
  router.push(`/drawings/${route.params.id}/history`)
}

const handleLevelReview = () => {
  reviewForm.final_level = drawing.confidentiality_level
  reviewForm.reason = ''
  reviewDialogVisible.value = true
}

const handleApprove = async () => {
  if (!reviewForm.final_level) {
    ElMessage.warning('请选择最终等级')
    return
  }

  submitting.value = true
  try {
    await api.reviews.approve(route.params.id, {
      final_level: reviewForm.final_level,
      reason: reviewForm.reason
    })
    ElMessage.success('审核通过')
    reviewDialogVisible.value = false
    loadDrawing()
  } catch (error) {
    console.error('审核失败:', error)
    ElMessage.error('审核失败：' + error.message)
  } finally {
    submitting.value = false
  }
}

const handleReject = async () => {
  if (!reviewForm.reason) {
    ElMessage.warning('请填写驳回原因')
    return
  }

  try {
    await ElMessageBox.confirm('确认驳回此图纸的审核吗？', '驳回确认', { type: 'warning' })

    submitting.value = true
    try {
      await api.reviews.reject(route.params.id, {
        reason: reviewForm.reason
      })
      ElMessage.success('已驳回')
      reviewDialogVisible.value = false
      loadDrawing()
    } catch (error) {
      console.error('驳回失败:', error)
      ElMessage.error('驳回失败：' + error.message)
    } finally {
      submitting.value = false
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('驳回失败:', error)
    }
  }
}
</script>

<style scoped>
.drawing-detail-page {
  padding: 0;
}

.page-content {
  margin-top: 15px;
  position: relative;
}

.archived-watermark {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-45deg);
  font-size: 80px;
  font-weight: bold;
  color: rgba(245, 108, 108, 0.15);
  pointer-events: none;
  z-index: 1000;
  white-space: nowrap;
}

::v-deep .archived-watermark-dialog {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%) rotate(-45deg);
  font-size: 60px;
  font-weight: bold;
  color: rgba(245, 108, 108, 0.2);
  pointer-events: none;
  z-index: 2000;
  white-space: nowrap;
}

.info-card {
  min-height: 200px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-form {
  margin-top: 10px;
}

.level-info {
  text-align: center;
  padding: 10px 0;
}

.file-info {
  display: flex;
  align-items: center;
  padding: 15px 0;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  margin-bottom: 15px;
}

.file-icon {
  font-size: 48px;
  color: #409EFF;
  margin-right: 15px;
}

.file-meta {
  flex: 1;
}

.file-name {
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.file-size {
  font-size: 12px;
  color: #909399;
}

.file-actions {
  margin-bottom: 10px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

/* 打印样式 */
.print-content {
  font-family: 'Microsoft YaHei', Arial, sans-serif;
}

.print-header {
  text-align: center;
  margin-bottom: 20px;
  border-bottom: 2px solid #409EFF;
  padding-bottom: 15px;
}

.print-header h1 {
  color: #409EFF;
  font-size: 24px;
  margin-bottom: 5px;
}

.print-subtitle {
  color: #409EFF;
  font-size: 14px;
  font-weight: bold;
  margin: 5px 0;
}

.print-date {
  color: #666;
  font-size: 12px;
}

.print-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
}

.print-table th,
.print-table td {
  border: 1px solid #ddd;
  padding: 10px 8px;
  text-align: left;
}

.print-table th {
  background: #f5f7fa;
  width: 120px;
  font-weight: 600;
  color: #606266;
}

.print-section {
  margin-top: 25px;
}

.print-section h3 {
  font-size: 16px;
  color: #303133;
  margin-bottom: 10px;
  padding-left: 10px;
  border-left: 4px solid #409EFF;
}

.versions-table th,
.versions-table td {
  text-align: center;
}

/* 打印高亮样式 */
.level-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-weight: bold;
  color: white;
}

.level-A {
  background: #F56C6C;
}

.level-B {
  background: #E6A23C;
}

.level-C {
  background: #909399;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-weight: bold;
  color: white;
}

.status-pending {
  background: #E6A23C;
}

.status-approved {
  background: #67C23A;
}

.status-rejected {
  background: #F56C6C;
}

.keyword-tag {
  display: inline-block;
  padding: 2px 8px;
  margin-right: 5px;
  background: #f0f9ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  color: #1890ff;
  font-size: 12px;
}
</style>

