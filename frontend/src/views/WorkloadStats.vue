<template>
  <div class="workload-page">
    <div class="page-header">
      <h2>工作量统计</h2>
      <div class="date-selector">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          :shortcuts="dateShortcuts"
          @change="handleDateRangeChange"
          style="width: 280px"
        />
      </div>
    </div>

    <!-- 汇总卡片 -->
    <el-row :gutter="20" class="summary-cards">
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-icon" style="background: #409EFF">
            <el-icon><Document /></el-icon>
          </div>
          <div class="summary-info">
            <div class="summary-value">{{ summary.total_drawings }}</div>
            <div class="summary-label">新增图纸</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-icon" style="background: #67c23a">
            <el-icon><Upload /></el-icon>
          </div>
          <div class="summary-info">
            <div class="summary-value">{{ summary.total_versions }}</div>
            <div class="summary-label">版本上传</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-icon" style="background: #e6a23c">
            <el-icon><Checked /></el-icon>
          </div>
          <div class="summary-info">
            <div class="summary-value">{{ summary.total_reviews }}</div>
            <div class="summary-label">保密审定</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="summary-card">
          <div class="summary-icon" style="background: #f56c6c">
            <el-icon><User /></el-icon>
          </div>
          <div class="summary-info">
            <div class="summary-value">{{ summary.active_users_today }}</div>
            <div class="summary-label">今日活跃</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 个人贡献排行 -->
    <el-card class="table-card" style="margin-top: 20px">
      <template #header>
        <span>个人贡献排行</span>
      </template>

      <el-table :data="workloadList" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="user_name" label="姓名" width="120" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ getRoleLabel(row.role_id) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建图纸" width="120">
          <template #default="{ row }">
            <span class="count">{{ row.drawings_created }}</span>
          </template>
        </el-table-column>
        <el-table-column label="上传版本" width="120">
          <template #default="{ row }">
            <span class="count">{{ row.versions_uploaded }}</span>
          </template>
        </el-table-column>
        <el-table-column label="审定图纸" width="120">
          <template #default="{ row }">
            <span class="count">{{ row.drawings_reviewed }}</span>
          </template>
        </el-table-column>
        <el-table-column label="总贡献" prop="total_contributions" width="120">
          <template #default="{ row }">
            <el-tag type="success" size="small">{{ row.total_contributions }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="贡献占比" min-width="200">
          <template #default="{ row }">
            <div class="contribution-bar">
              <div
                class="bar-fill"
                :style="{ width: getContributionPercent(row.total_contributions) + '%' }"
              ></div>
              <span class="bar-text">{{ getContributionPercent(row.total_contributions) }}%</span>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Document, Upload, Checked, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { api } from '../utils/api'

const loading = ref(false)
const dateRange = ref([])
const workloadList = ref([])
const summary = ref({
  total_drawings: 0,
  total_versions: 0,
  total_reviews: 0,
  active_users_today: 0,
  days: 30
})

// 日期范围快捷选项
const dateShortcuts = [
  {
    text: '近7天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7)
      return [start, end]
    }
  },
  {
    text: '近14天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 14)
      return [start, end]
    }
  },
  {
    text: '近30天',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
      return [start, end]
    }
  }
]

// 监听日期范围变化
watch(dateRange, (newVal) => {
  console.log('日期范围变化:', newVal)
  loadWorkloadData()
}, { deep: true })

const getRoleLabel = (roleId) => {
  const map = {
    'role_admin': '管理员',
    'role_cto': 'CTO',
    'role_project_manager': '项目负责人',
    'role_engineer': '工程师',
    'role_designer': '设计师',
    'role_reviewer': '审定人',
    'role_guest': '访客'
  }
  return map[roleId] || roleId
}

const getContributionPercent = (contribution) => {
  const total = summary.value.total_versions + summary.value.total_drawings + summary.value.total_reviews
  if (total === 0) return 0
  return Math.round((contribution / total) * 100)
}

const handleDateRangeChange = () => {
  console.log('日期选择变化，触发重新加载')
  loadWorkloadData()
}

const loadWorkloadData = async () => {
  loading.value = true
  try {
    // 格式化日期为 YYYY-MM-DD
    let startDateStr = null
    let endDateStr = null
    if (dateRange.value && dateRange.value.length === 2) {
      const start = new Date(dateRange.value[0])
      const end = new Date(dateRange.value[1])
      startDateStr = start.toISOString().split('T')[0]
      endDateStr = end.toISOString().split('T')[0]
    }

    console.log('加载工作量数据，日期范围:', startDateStr, '至', endDateStr)

    const [summaryRes, statsRes] = await Promise.all([
      api.workload.getSummary(startDateStr, endDateStr),
      api.workload.getStats(startDateStr, endDateStr)
    ])

    if (summaryRes.data) {
      summary.value = summaryRes.data
    }

    workloadList.value = statsRes.data || []
  } catch (error) {
    console.error('加载工作量统计失败:', error)
    ElMessage.error('加载工作量统计失败：' + error.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // 默认近30天
  const end = new Date()
  const start = new Date()
  start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
  dateRange.value = [start, end]
  loadWorkloadData()
})
</script>

<style scoped>
.workload-page {
  padding: 0;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.date-selector {
  margin-left: auto;
}

.summary-cards {
  margin-bottom: 0;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px;
}

.summary-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24px;
}

.summary-info {
  flex: 1;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.summary-label {
  font-size: 13px;
  color: #909399;
  margin-top: 5px;
}

.table-card {
  min-height: 400px;
}

.count {
  font-weight: bold;
  color: #409EFF;
}

.contribution-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.bar-fill {
  height: 20px;
  background: linear-gradient(90deg, #409EFF 0%, #79bbff 100%);
  border-radius: 4px;
  min-width: 10px;
  max-width: 150px;
}

.bar-text {
  color: #606266;
  font-size: 13px;
}
</style>
