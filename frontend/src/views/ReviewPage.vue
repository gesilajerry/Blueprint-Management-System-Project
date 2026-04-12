<template>
  <div class="review-page">
    <div class="page-header">
      <h2>保密等级审核</h2>
      <el-alert
        title="审定人：当前登录的审定人员"
        type="warning"
        :closable="false"
        show-icon
        style="width: auto; display: inline-block;"
      />
    </div>

    <!-- 待审核列表 -->
    <el-card class="table-card" style="margin-top: 15px">
      <template #header>
        <div class="card-header">
          <span>待审核图纸</span>
          <el-badge :value="pendingList.length" type="danger" style="margin-left: 10px" />
        </div>
      </template>

      <el-table :data="pendingList" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="drawing_no" label="图号" width="200" />
        <el-table-column prop="name" label="图纸名称" min-width="180" />
        <el-table-column prop="version_no" label="版本号" width="80">
          <template #default="{ row }">
            <el-tag type="primary" size="small">{{ row.version_no }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="所属产品" width="150" />
        <el-table-column prop="department_name" label="所属部门" width="100" />
        <el-table-column prop="creator_name" label="创建人" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ row.created_at ? row.created_at.replace('T', ' ').substring(0, 16) : '' }}
          </template>
        </el-table-column>

        <el-table-column label="初定结果" width="120">
          <template #default="{ row }">
            <div style="display: flex; flex-direction: column; gap: 5px">
              <el-tag :type="row.confidentiality_level === 'A' ? 'danger' : row.confidentiality_level === 'B' ? 'warning' : 'info'" size="small">
                {{ row.confidentiality_level }}类
              </el-tag>
              <el-tag v-if="row.is_core_part" type="danger" size="small">核心部件</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleViewDetail(row)">详情</el-button>
            <el-button link type="primary" @click="handleReview(row)">审核</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 审核记录 -->
    <el-card class="table-card" style="margin-top: 15px">
      <template #header>
        <span>审定历史记录</span>
      </template>

      <el-table :data="reviewHistory" stripe style="width: 100%">
        <el-table-column prop="drawingNo" label="图号" width="180" />
        <el-table-column prop="name" label="图纸名称" min-width="150" />
        <el-table-column label="等级变更" width="150">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 5px">
              <el-tag :type="getLevelTagType(row.oldLevel)" size="small">{{ row.oldLevel }}类</el-tag>
              <el-icon style="color: #909399"><Right /></el-icon>
              <el-tag :type="getLevelTagType(row.newLevel)" size="small">{{ row.newLevel }}类</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="reviewReason" label="审定意见" min-width="200" show-overflow-tooltip />
        <el-table-column prop="reviewer" label="审定人" width="100" />
        <el-table-column prop="reviewTime" label="审定时间" width="160" />
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="historyPagination.page"
          v-model:page-size="historyPagination.size"
          :page-sizes="[10, 20, 50]"
          :total="historyPagination.total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleHistorySizeChange"
          @current-change="handleHistoryPageChange"
        />
      </div>
    </el-card>

    <!-- 图纸详情抽屉 -->
    <el-drawer
      v-model="detailDrawerVisible"
      title="图纸详情"
      size="700px"
      :before-close="handleCloseDetail"
    >
      <el-tabs v-if="currentDrawing">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="图号">{{ currentDrawing.drawing_no }}</el-descriptions-item>
            <el-descriptions-item label="图纸名称">{{ currentDrawing.name }}</el-descriptions-item>
            <el-descriptions-item label="版本号">
              <el-tag type="primary" size="small">{{ currentDrawing.version_no }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ currentDrawing.created_at ? currentDrawing.created_at.replace('T', ' ').substring(0, 16) : '' }}
            </el-descriptions-item>
            <el-descriptions-item label="所属产品">{{ currentDrawing.product_name }}</el-descriptions-item>
            <el-descriptions-item label="所属部门">{{ currentDrawing.department_name }}</el-descriptions-item>
            <el-descriptions-item label="创建人">{{ currentDrawing.creator_name }}</el-descriptions-item>
            <el-descriptions-item label="是否核心部件">
              <el-tag :type="currentDrawing.is_core_part ? 'danger' : 'info'" size="small">
                {{ currentDrawing.is_core_part ? '是' : '否' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="初定等级">
              <el-tag :type="currentDrawing.confidentiality_level === 'A' ? 'danger' : currentDrawing.confidentiality_level === 'B' ? 'warning' : 'info'" size="small">
                {{ currentDrawing.confidentiality_level }}类
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <!-- 知识沉淀信息 -->
        <el-tab-pane label="知识沉淀信息">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用途背景">
              <div style="white-space: pre-wrap; line-height: 1.6;">
                {{ currentDrawing.purpose || '未填写' }}
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="关键材料">
              {{ currentDrawing.material || '未填写' }}
            </el-descriptions-item>
            <el-descriptions-item label="关键尺寸">
              {{ currentDrawing.dimensions || '未填写' }}
            </el-descriptions-item>
            <el-descriptions-item label="保密要点">
              <div style="white-space: pre-wrap; line-height: 1.6;">
                {{ currentDrawing.secret_points || '未填写' }}
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button type="primary" @click="handleReviewFromDetail">审核</el-button>
        <el-button @click="detailDrawerVisible = false">关闭</el-button>
      </template>
    </el-drawer>

    <!-- 审核对话框 -->
    <el-dialog
      v-model="reviewDialogVisible"
      title="保密等级审核"
      width="800px"
      :before-close="handleCloseReview"
    >
      <el-tabs v-if="currentDrawing">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="图号">{{ currentDrawing.drawing_no }}</el-descriptions-item>
            <el-descriptions-item label="图纸名称">{{ currentDrawing.name }}</el-descriptions-item>
            <el-descriptions-item label="版本号">
              <el-tag type="primary" size="small">{{ currentDrawing.version_no }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ currentDrawing.created_at ? currentDrawing.created_at.replace('T', ' ').substring(0, 16) : '' }}
            </el-descriptions-item>
            <el-descriptions-item label="所属产品">{{ currentDrawing.product_name }}</el-descriptions-item>
            <el-descriptions-item label="所属部门">{{ currentDrawing.department_name }}</el-descriptions-item>
            <el-descriptions-item label="创建人">{{ currentDrawing.creator_name }}</el-descriptions-item>
            <el-descriptions-item label="是否核心部件">
              <el-tag :type="currentDrawing.is_core_part ? 'danger' : 'info'" size="small">
                {{ currentDrawing.is_core_part ? '是' : '否' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="初定等级">
              <el-tag :type="currentDrawing.confidentiality_level === 'A' ? 'danger' : currentDrawing.confidentiality_level === 'B' ? 'warning' : 'info'" size="small">
                {{ currentDrawing.confidentiality_level }}类
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>

        <!-- 知识沉淀信息 -->
        <el-tab-pane label="知识沉淀信息">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用途背景">
              <div style="white-space: pre-wrap; line-height: 1.6;">
                {{ currentDrawing.purpose || '未填写' }}
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="关键材料">
              {{ currentDrawing.material || '未填写' }}
            </el-descriptions-item>
            <el-descriptions-item label="关键尺寸">
              {{ currentDrawing.dimensions || '未填写' }}
            </el-descriptions-item>
            <el-descriptions-item label="保密要点">
              <div style="white-space: pre-wrap; line-height: 1.6;">
                {{ currentDrawing.secret_points || '未填写' }}
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>

      <el-divider />

      <el-form :model="reviewForm" label-width="100px">
        <el-form-item label="最终定级" required>
          <el-radio-group v-model="reviewForm.finalLevel">
            <el-radio value="A">A 类</el-radio>
            <el-radio value="B">B 类</el-radio>
            <el-radio value="C">C 类</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="调整原因" required v-if="reviewForm.finalLevel !== currentDrawing?.confidentiality_level">
          <el-input
            v-model="reviewForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请说明调整保密等级的原因"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmReview">确认审核</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Right } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../utils/api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

const pendingList = ref([])
const reviewHistory = ref([])
const loading = ref(false)

const historyPagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const detailDrawerVisible = ref(false)
const reviewDialogVisible = ref(false)
const currentDrawing = ref(null)
const reviewForm = reactive({
  finalLevel: '',
  reason: ''
})

// 加载待审核列表
const loadPendingReviews = async () => {
  loading.value = true
  try {
    const res = await api.reviews.getPending()
    pendingList.value = res.data || []
    if (pendingList.value.length === 0) {
      ElMessage.info('暂无待审核的图纸')
    }
  } catch (error) {
    console.error('加载待审核列表失败:', error)
    if (error.message.includes('403') || error.message.includes('权限')) {
      ElMessage.error('您没有权限访问保密审核功能')
    } else {
      ElMessage.error('加载待审核列表失败：' + error.message)
    }
  } finally {
    loading.value = false
  }
}

// 加载审定历史记录
const loadReviewHistory = async () => {
  try {
    // 使用新的全局审定历史接口（带分页）
    const res = await api.reviews.getAllHistory({
      page: historyPagination.page,
      size: historyPagination.size
    })
    const data = res.data || {}
    const historyList = data.items || []

    reviewHistory.value = historyList.map(h => ({
      drawingNo: h.drawing_no || h.drawingId || '未知',
      name: h.drawing_name || h.drawingName || '未知',
      oldLevel: h.old_level || '-',
      newLevel: h.new_level,
      reviewReason: h.reason || '无',
      reviewer: h.reviewer_name || '未知',
      reviewTime: h.created_at ? new Date(h.created_at).toLocaleString('zh-CN') : ''
    }))

    historyPagination.total = data.total || 0

    if (reviewHistory.value.length === 0) {
      ElMessage.info('暂无审定记录')
    }
  } catch (error) {
    console.error('加载审定历史失败:', error)
    reviewHistory.value = []
  }
}

const handleHistorySizeChange = (size) => {
  historyPagination.size = size
  historyPagination.page = 1
  loadReviewHistory()
}

const handleHistoryPageChange = (page) => {
  historyPagination.page = page
  loadReviewHistory()
}

onMounted(() => {
  loadPendingReviews()
  loadReviewHistory()
})

const getLevelTagType = (level) => {
  const map = { A: 'danger', B: 'warning', C: 'info' }
  return map[level] || 'info'
}

const getLevelLabel = (level) => {
  const map = { A: 'A 类 - 核心机密', B: 'B 类 - 重要', C: 'C 类 - 一般' }
  return map[level] || level
}

const handleViewDetail = (row) => {
  currentDrawing.value = row
  detailDrawerVisible.value = true
}

const handleReviewFromDetail = () => {
  detailDrawerVisible.value = false
  reviewDialogVisible.value = true
}

const handleReview = (row) => {
  currentDrawing.value = row
  reviewForm.finalLevel = row.confidentiality_level
  reviewForm.reason = ''
  reviewDialogVisible.value = true
}

const handleCloseDetail = (done) => {
  done()
}

const handleCloseReview = (done) => {
  done()
}

const handleConfirmReview = async () => {
  if (!reviewForm.finalLevel) {
    ElMessage.warning('请选择最终定级')
    return
  }

  if (reviewForm.finalLevel !== currentDrawing.value?.confidentiality_level && !reviewForm.reason) {
    ElMessage.warning('调整等级必须填写原因')
    return
  }

  try {
    await api.reviews.approve(currentDrawing.value.id, {
      final_level: reviewForm.finalLevel,
      reason: reviewForm.reason
    })

    ElMessage.success('审核完成')
    reviewDialogVisible.value = false

    // 重新加载列表
    loadPendingReviews()
    loadReviewHistory()
  } catch (error) {
    ElMessage.error('审核失败：' + error.message)
  }
}
</script>

<style scoped>
.review-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 15px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.card-header {
  display: flex;
  align-items: center;
}

.table-card {
  min-height: 300px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
