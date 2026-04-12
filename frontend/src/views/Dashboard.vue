<template>
  <div class="dashboard-page">
    <div class="page-header">
      <h2>统计看板</h2>
      <el-button @click="handleRefresh">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #409EFF">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalDrawings }}</div>
              <div class="stat-label">图纸总量</div>
            </div>
          </div>
          <div class="stat-footer">
            <span class="trend-up">
              <el-icon><Top /></el-icon>
              {{ stats.thisMonthNew }} 本月新增
            </span>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #f56c6c">
              <el-icon><Lock /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.levelA }}</div>
              <div class="stat-label">A 类 - 核心机密</div>
            </div>
          </div>
          <div class="stat-footer">
            <span class="trend-up">
              <el-icon><Top /></el-icon>
              {{ stats.thisMonthNew }} 本月新增
            </span>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #e6a23c">
              <el-icon><Checked /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.pendingReviews }}</div>
              <div class="stat-label">待审核图纸</div>
            </div>
          </div>
          <div class="stat-footer">
            <span class="trend-text" style="color: #e6a23c">
              待及时处理
            </span>
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon" style="background: #67c23a">
              <el-icon><DataLine /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.thisMonthVersions }}</div>
              <div class="stat-label">本月版本更新</div>
            </div>
          </div>
          <div class="stat-footer">
            <span class="trend-up">
              <el-icon><Top /></el-icon>
              实时更新
            </span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 保密等级分布 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>保密等级分布</span>
          </template>
          <div class="chart-container">
            <div class="level-dist">
              <div class="level-item" v-if="stats.totalDrawings > 0">
                <div class="level-bar" :style="{ width: (stats.levelA / stats.totalDrawings * 100) + '%', background: '#f56c6c' }"></div>
                <span class="level-label">A 类 - 核心机密</span>
                <span class="level-count">{{ stats.levelA }} 份</span>
              </div>
              <div class="level-item" v-if="stats.totalDrawings > 0">
                <div class="level-bar" :style="{ width: (stats.levelB / stats.totalDrawings * 100) + '%', background: '#e6a23c' }"></div>
                <span class="level-label">B 类 - 重要</span>
                <span class="level-count">{{ stats.levelB }} 份</span>
              </div>
              <div class="level-item" v-if="stats.totalDrawings > 0">
                <div class="level-bar" :style="{ width: (stats.levelC / stats.totalDrawings * 100) + '%', background: '#909399' }"></div>
                <span class="level-label">C 类 - 一般</span>
                <span class="level-count">{{ stats.levelC }} 份</span>
              </div>
              <div class="level-item" v-if="stats.totalDrawings === 0">
                <span class="level-label">暂无数据</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 近7天图纸上传趋势 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>近7天图纸上传趋势</span>
          </template>
          <div class="chart-container">
            <div class="trend-chart">
              <div class="trend-bars">
                <div class="trend-bar-group" v-for="(day, dayIndex) in weeklyTrend" :key="dayIndex">
                  <div class="trend-bar-stack">
                    <div
                      v-for="(item, prodIndex) in day.byProduct"
                      :key="prodIndex"
                      class="trend-bar-segment"
                      :style="{
                        height: (item.count / (day.total || 1) * 100) + '%',
                        backgroundColor: getProductColor(prodIndex)
                      }"
                      :title="item.productName + ': ' + item.count"
                    ></div>
                  </div>
                  <span class="trend-label">{{ day.label }}</span>
                  <span class="trend-total">{{ day.total }}</span>
                </div>
              </div>
              <div class="trend-legend" v-if="productColors.length > 0">
                <span v-for="(color, idx) in productColors" :key="idx" class="legend-item">
                  <span class="legend-color" :style="{ backgroundColor: color }"></span>
                  {{ getProductNameByIndex(idx) }}
                </span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 产品图纸统计 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="24">
        <el-card class="table-card">
          <template #header>
            <span>各项目图纸统计</span>
          </template>

          <el-table :data="productStats" stripe style="width: 100%">
            <el-table-column prop="code" label="立项编号" width="180" />
            <el-table-column prop="name" label="产品/项目名称" min-width="200" />
            <el-table-column prop="total" label="图纸总数" width="100" />
            <el-table-column label="保密等级分布" width="250">
              <template #default="{ row }">
                <div class="level-distribution">
                  <el-tag type="danger" size="small">A 类 {{ row.levelA }}</el-tag>
                  <el-tag type="warning" size="small" style="margin: 0 5px">B 类 {{ row.levelB }}</el-tag>
                  <el-tag size="small">C 类 {{ row.levelC }}</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="latestVersion" label="最新版本日期" width="140" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button link type="primary" @click="handleViewProject(row)">查看详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card class="activity-card">
          <template #header>
            <span>最近上传</span>
          </template>

          <el-timeline>
            <el-timeline-item
              v-for="(item, index) in recentUploads"
              :key="index"
              :timestamp="item.created_at ? item.created_at.replace('T', ' ').substring(0, 16) : ''"
              placement="top"
            >
              <el-card>
                <p><strong>用户</strong> 上传了 <strong>{{ item.name }}</strong></p>
                <p style="color: #909399; font-size: 12px">{{ item.drawing_no }} · {{ item.version }}</p>
              </el-card>
            </el-timeline-item>
            <el-timeline-item v-if="recentUploads.length === 0">
              <span style="color: #909399">暂无上传记录</span>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="activity-card">
          <template #header>
            <span>最近审核</span>
          </template>

          <el-timeline>
            <el-timeline-item timestamp="04-10 08:00" placement="top">
              <el-card>
                <p><strong>李审定</strong> 审核了 <strong>机器人关节驱动模块</strong></p>
                <p style="color: #909399; font-size: 12px">
                  <span style="color: #909399; text-decoration: line-through">B 类</span>
                  <el-icon style="color: #909399"><Right /></el-icon>
                  <el-tag type="danger" size="small">A 类</el-tag>
                </p>
              </el-card>
            </el-timeline-item>
            <el-timeline-item timestamp="04-08 15:30" placement="top">
              <el-card>
                <p><strong>李审定</strong> 审核了 <strong>电池模组连接片</strong></p>
                <p style="color: #909399; font-size: 12px">
                  维持 <el-tag type="warning" size="small">B 类</el-tag>
                </p>
              </el-card>
            </el-timeline-item>
            <el-timeline-item timestamp="04-08 10:00" placement="top">
              <el-card>
                <p><strong>李审定</strong> 审核了 <strong>外壳固定螺钉</strong></p>
                <p style="color: #909399; font-size: 12px">
                  <span style="color: #909399; text-decoration: line-through">B 类</span>
                  <el-icon style="color: #909399"><Right /></el-icon>
                  <el-tag size="small">C 类</el-tag>
                </p>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Document, Lock, Checked, DataLine, Refresh, Top, Right
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { api } from '../utils/api'

const router = useRouter()

const stats = ref({
  totalDrawings: 0,
  levelA: 0,
  levelB: 0,
  levelC: 0,
  pendingReviews: 0,
  thisMonthVersions: 0,
  thisMonthNew: 0
})

const productStats = ref([])
const recentUploads = ref([])
const weeklyTrend = ref([])
const productColors = ref([])
const productNameMap = ref({})

// 产品颜色数组
const colorPalette = [
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399',
  '#19A2DE', '#1ABC9C', '#9B59B6', '#34495E', '#2ECC71'
]

const getProductColor = (index) => {
  return colorPalette[index % colorPalette.length]
}

const getProductNameByIndex = (index) => {
  const keys = Object.keys(productNameMap.value)
  return productNameMap.value[keys[index]] || `产品${index + 1}`
}

const handleRefresh = async () => {
  await loadDashboardData()
  ElMessage.success('数据已刷新')
}

// 加载仪表板数据
const loadDashboardData = async () => {
  try {
    // 使用专门的看板API（不过滤权限，返回全部数据）
    const [statsRes, productStatsRes, weeklyTrendRes, recentUploadsRes] = await Promise.all([
      api.dashboard.getStats(),
      api.dashboard.getProductStats(),
      api.dashboard.getWeeklyTrend(),
      api.dashboard.getRecentUploads()
    ])

    // 统计数据
    if (statsRes.data) {
      stats.value.totalDrawings = statsRes.data.totalDrawings || 0
      stats.value.levelA = statsRes.data.levelA || 0
      stats.value.levelB = statsRes.data.levelB || 0
      stats.value.levelC = statsRes.data.levelC || 0
      stats.value.pendingReviews = statsRes.data.pendingReviews || 0
      stats.value.thisMonthNew = statsRes.data.thisMonthNew || 0
      stats.value.thisMonthVersions = statsRes.data.thisMonthVersions || 0
    }

    // 产品统计
    productStats.value = (productStatsRes.data || []).map(p => ({
      code: p.code,
      name: p.name,
      id: p.id,
      total: p.total || 0,
      levelA: p.levelA || 0,
      levelB: p.levelB || 0,
      levelC: p.levelC || 0,
      latestVersion: p.latestVersion || '-'
    }))

    // 近7天上传趋势（按产品分组）
    const trendData = weeklyTrendRes.data || []
    weeklyTrend.value = trendData.map(w => ({
      date: w.date,
      label: w.label,
      weekday: w.weekday,
      total: w.total || 0,
      percentage: w.percentage || 20,
      byProduct: w.byProduct || []
    }))

    // 收集所有产品名称用于图例
    const allProducts = new Set()
    const productMap = {}
    trendData.forEach(day => {
      (day.byProduct || []).forEach((item, idx) => {
        if (!productMap[item.productId]) {
          productMap[item.productId] = item.productName
          allProducts.add(item.productName)
        }
      })
    })
    productNameMap.value = productMap
    productColors.value = Array.from(allProducts).map((_, idx) => colorPalette[idx % colorPalette.length])

    // 最近上传
    recentUploads.value = (recentUploadsRes.data || []).map(u => ({
      drawing_no: u.drawing_no,
      name: u.name,
      created_at: u.created_at,
      version: u.version || 'V1.0'
    }))

  } catch (error) {
    console.error('加载仪表板数据失败:', error)
  }
}

onMounted(() => {
  loadDashboardData()
})

const handleViewProject = (row) => {
  router.push(`/drawings?product_id=${row.id}`)
}
</script>

<style scoped>
.dashboard-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.stat-cards {
  margin-bottom: 0;
}

.stat-card {
  min-height: 140px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 28px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 5px;
}

.stat-footer {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
  font-size: 12px;
}

.trend-up {
  color: #67c23a;
  display: flex;
  align-items: center;
  gap: 3px;
}

.trend-text {
  font-size: 12px;
}

.chart-card {
  min-height: 280px;
}

.chart-container {
  padding: 10px 0;
}

.level-dist {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
}

.level-item {
  display: flex;
  align-items: center;
  gap: 15px;
}

.level-bar {
  height: 24px;
  border-radius: 4px;
  min-width: 50px;
}

.level-label {
  width: 120px;
  font-size: 13px;
  color: #606266;
}

.level-count {
  font-weight: bold;
  color: #303133;
}

.trend-chart {
  padding: 20px;
  height: 220px;
}

.trend-bars {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 160px;
  padding-bottom: 5px;
  border-bottom: 1px solid #dcdfe6;
}

.trend-bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  flex: 1;
}

.trend-bar-stack {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  width: 50px;
  height: 140px;
  border-radius: 4px 4px 0 0;
  overflow: hidden;
}

.trend-bar-segment {
  width: 100%;
  min-height: 4px;
  transition: height 0.3s;
}

.trend-label {
  font-size: 11px;
  color: #909399;
}

.trend-total {
  font-size: 12px;
  font-weight: bold;
  color: #409EFF;
}

.trend-legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #ebeef5;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #606266;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.table-card {
  min-height: 300px;
}

.level-distribution {
  display: flex;
  align-items: center;
}

.activity-card {
  min-height: 350px;
}
</style>
