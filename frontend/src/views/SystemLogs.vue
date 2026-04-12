<template>
  <div class="logs-page">
    <div class="page-header">
      <h2>系统日志</h2>
      <el-button @click="handleExport">
        <el-icon><Download /></el-icon>
        导出日志
      </el-button>
    </div>

    <el-alert
      title="系统日志说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 15px"
    >
      <template #title>
        <div style="font-size: 13px">
          记录系统所有操作行为，用于审计和追溯。包括用户登录、图纸操作、系统配置变更等。
          <br>
          <span style="color: #909399; font-size: 12px">日志自动保留 180 天，支持按条件筛选和导出</span>
        </div>
      </template>
    </el-alert>

    <el-card class="table-card">
      <!-- 搜索区 -->
      <el-form :inline="true" class="search-form" style="margin-bottom: 15px">
        <el-form-item label="操作人">
          <el-select v-model="searchForm.user_id" placeholder="全部" clearable style="width: 150px">
            <el-option
              v-for="user in userList"
              :key="user.id"
              :label="user.name || user.username"
              :value="user.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="操作类型">
          <el-select v-model="searchForm.action" placeholder="全部" clearable style="width: 150px">
            <el-option label="登录" value="LOGIN_SUCCESS" />
            <el-option label="创建图纸" value="CREATE_DRAWING" />
            <el-option label="上传版本" value="UPLOAD_VERSION" />
            <el-option label="审核" value="APPROVE_REVIEW" />
            <el-option label="导出" value="EXPORT" />
          </el-select>
        </el-form-item>

        <el-form-item label="资源类型">
          <el-select v-model="searchForm.resource_type" placeholder="全部" clearable style="width: 120px">
            <el-option label="图纸" value="drawing" />
            <el-option label="用户" value="user" />
            <el-option label="部门" value="department" />
            <el-option label="产品" value="product" />
          </el-select>
        </el-form-item>

        <el-form-item label="日期范围">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 240px"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="280" />
        <el-table-column prop="user_name" label="操作人" width="100" />
        <el-table-column prop="action" label="操作类型" width="150">
          <template #default="{ row }">
            <el-tag :type="getActionTagType(row.action)" size="small">
              {{ getActionLabel(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resource_type" label="资源类型" width="100" />
        <el-table-column prop="resource_id" label="资源 ID" width="200" />
        <el-table-column prop="description" label="操作描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP 地址" width="140" />
        <el-table-column prop="created_at" label="操作时间" width="170">
          <template #default="{ row }">
            {{ row.created_at ? row.created_at.replace('T', ' ').substring(0, 16) : '' }}
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { api } from '../utils/api'

const loading = ref(false)
const userList = ref([])

const searchForm = reactive({
  user_id: '',
  action: '',
  resource_type: '',
  dateRange: []
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const tableData = ref([])

// 加载用户列表
const loadUsers = async () => {
  try {
    const res = await api.users.list({ page: 1, size: 100 })
    userList.value = res.data?.items || []
  } catch (error) {
    console.error('加载用户列表失败:', error)
  }
}

// 加载日志列表
const loadLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }

    if (searchForm.user_id) params.user_id = searchForm.user_id
    if (searchForm.action) params.action = searchForm.action
    if (searchForm.resource_type) params.resource_type = searchForm.resource_type
    if (searchForm.dateRange && searchForm.dateRange.length === 2) {
      params.start_date = searchForm.dateRange[0]
      params.end_date = searchForm.dateRange[1]
    }

    const res = await api.logs.list(params)
    tableData.value = res.data?.items || []
    pagination.total = res.data?.total || 0

    // 加载用户名称
    const userIds = [...new Set(tableData.value.map(item => item.user_id))]
    const usersMap = {}
    for (const id of userIds) {
      try {
        const userRes = await api.users.get(id)
        usersMap[id] = userRes.data?.name || userRes.data?.username || '未知'
      } catch (e) {
        usersMap[id] = '未知'
      }
    }
    tableData.value.forEach(item => {
      item.user_name = usersMap[item.user_id] || '未知'
    })
  } catch (error) {
    console.error('加载日志失败:', error)
    ElMessage.error('加载日志失败：' + error.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadUsers()
  loadLogs()
})

const getActionLabel = (action) => {
  const map = {
    'LOGIN_SUCCESS': '登录成功',
    'LOGIN_FAILED': '登录失败',
    'LOGOUT': '登出',
    'CREATE_DRAWING': '创建图纸',
    'UPDATE_DRAWING': '更新图纸',
    'DELETE_DRAWING': '作废图纸',
    'UPLOAD_VERSION': '上传版本',
    'APPROVE_REVIEW': '审核通过',
    'REJECT_REVIEW': '审核驳回',
    'CREATE_USER': '创建用户',
    'UPDATE_USER': '更新用户',
    'EXPORT': '导出'
  }
  return map[action] || action
}

const getActionTagType = (action) => {
  if (action.includes('LOGIN') || action.includes('LOGOUT')) return 'info'
  if (action.includes('CREATE')) return 'success'
  if (action.includes('UPDATE')) return 'warning'
  if (action.includes('DELETE') || action.includes('REJECT')) return 'danger'
  if (action.includes('REVIEW')) return 'warning'
  return 'info'
}

const handleSearch = () => {
  pagination.page = 1
  loadLogs()
}

const handleReset = () => {
  searchForm.user_id = ''
  searchForm.action = ''
  searchForm.resource_type = ''
  searchForm.dateRange = []
  pagination.page = 1
  loadLogs()
}

const handleExport = () => {
  ElMessage.success('日志导出功能开发中...')
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  loadLogs()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadLogs()
}
</script>

<style scoped>
.logs-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.table-card {
  min-height: 500px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
