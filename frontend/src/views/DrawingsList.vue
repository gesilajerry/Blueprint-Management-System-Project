<template>
  <div class="drawings-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>图纸管理</h2>
      <div style="display: flex; gap: 10px">
        <el-button type="success" @click="handleExport">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
        <el-button type="warning" @click="handleFullBackup" :loading="backupLoading" v-if="userStore.isAdmin()">
          <el-icon><Download /></el-icon>
          全量备份
        </el-button>
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新建图纸
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选区 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="图号/名称">
          <el-input
            v-model="searchForm.keyword"
            placeholder="请输入图号或名称"
            clearable
            style="width: 200px"
          />
        </el-form-item>

        <el-form-item label="所属产品">
          <el-select v-model="searchForm.product_id" placeholder="请选择" clearable style="width: 180px" :loading="productsLoading">
            <el-option
              v-for="p in products"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="项目组">
          <el-select v-model="searchForm.project_group_id" placeholder="请选择" clearable style="width: 150px" :loading="projectGroupsLoading">
            <el-option
              v-for="pg in projectGroups"
              :key="pg.id"
              :label="pg.name"
              :value="pg.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="项目负责人">
          <el-select v-model="searchForm.manager_id" placeholder="请选择" clearable style="width: 120px" :loading="usersLoading">
            <el-option
              v-for="u in projectLeaders"
              :key="u.id"
              :label="u.name"
              :value="u.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="上传人">
          <el-select v-model="searchForm.uploader_id" placeholder="请选择" clearable style="width: 120px" :loading="usersLoading">
            <el-option
              v-for="u in users"
              :key="u.id"
              :label="u.name"
              :value="u.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="创建人">
          <el-select v-model="searchForm.creator_id" placeholder="请选择" clearable style="width: 120px" :loading="usersLoading">
            <el-option
              v-for="u in users"
              :key="u.id"
              :label="u.name"
              :value="u.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="保密等级">
          <el-select v-model="searchForm.confidentiality_level" placeholder="请选择" clearable style="width: 120px">
            <el-option label="A 类 - 核心机密" value="A" />
            <el-option label="B 类 - 重要" value="B" />
            <el-option label="C 类 - 一般" value="C" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择" style="width: 120px">
            <el-option label="有效" value="active" />
            <el-option label="已作废" value="archived" />
            <el-option label="全部" value="all" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 表格区 -->
    <el-card class="table-card">
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading" :row-class-name="getRowClassName">
        <el-table-column prop="drawing_no" label="图号" width="180" />
        <el-table-column prop="name" label="图纸名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="version_no" label="版本号" width="90">
          <template #default="{ row }">
            <el-tag type="primary" size="small">{{ row.version_no || 'V1.0' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="保密等级" width="100">
          <template #default="{ row }">
            <el-tag :type="getLevelTagType(row.confidentiality_level)">
              {{ getLevelLabel(row.confidentiality_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="product_name" label="所属产品" min-width="150" show-overflow-tooltip />
        <el-table-column prop="project_group_name" label="项目组" width="120" />
        <el-table-column prop="project_manager" label="项目负责人" width="100" />
        <el-table-column prop="purpose" label="用途背景" min-width="120" show-overflow-tooltip />
        <el-table-column label="审定状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.review_status === 'approved' ? 'success' : row.review_status === 'rejected' ? 'danger' : 'info'" size="small">
              {{ row.review_status === 'approved' ? '已审定' : row.review_status === 'rejected' ? '已驳回' : '待审定' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="uploader_name" label="上传人" width="100" />
        <el-table-column prop="creator_name" label="创建人" width="100" />
        <el-table-column prop="uploaded_at" label="上传日期" width="120">
          <template #default="{ row }">
            {{ row.uploaded_at ? row.uploaded_at.substring(0, 10) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">详情</el-button>
            <el-button link type="primary" @click="handleUpload(row)" v-if="row.status !== 'archived'">上传版本</el-button>
            <el-dropdown trigger="click">
              <el-button link type="info">更多</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleHistory(row)">版本历史</el-dropdown-item>
                  <el-dropdown-item divided @click="handleReactivate(row)" v-if="row.status === 'archived'" style="color: #67c23a">重新激活</el-dropdown-item>
                  <el-dropdown-item divided @click="handleDelete(row)" style="color: #f56c6c" v-if="row.status !== 'archived'">作废</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
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
import { useRouter, useRoute } from 'vue-router'
import { Plus, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../utils/api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const loading = ref(false)
const backupLoading = ref(false)

const searchForm = reactive({
  keyword: '',
  product_id: '',
  project_group_id: '',
  manager_id: '',
  uploader_id: '',
  creator_id: '',
  confidentiality_level: '',
  status: 'active'
})

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const tableData = ref([])

// 加载数据
const products = ref([])
const projectGroups = ref([])
const users = ref([])
const projectLeaders = ref([])
const productsLoading = ref(false)
const projectGroupsLoading = ref(false)
const usersLoading = ref(false)

// 加载产品列表（只加载进行中的产品）
const loadProducts = async () => {
  productsLoading.value = true
  try {
    const res = await api.products.list({ page: 1, size: 100, status: 'active' })
    products.value = res.data?.items || []
  } catch (error) {
    console.error('加载产品列表失败:', error)
  } finally {
    productsLoading.value = false
  }
}

// 加载项目组列表（只加载进行中的）
const loadProjectGroups = async () => {
  projectGroupsLoading.value = true
  try {
    const res = await api.projectGroups.list({ page: 1, size: 100, status: 'active' })
    projectGroups.value = res.data?.items || []
  } catch (error) {
    console.error('加载项目组列表失败:', error)
  } finally {
    projectGroupsLoading.value = false
  }
}

// 加载用户列表（项目负责人）
const loadProjectLeaders = async () => {
  usersLoading.value = true
  try {
    const res = await api.users.list({ page: 1, size: 100, is_project_leader: true })
    projectLeaders.value = res.data?.items || []
  } catch (error) {
    console.error('加载项目负责人列表失败:', error)
  } finally {
    usersLoading.value = false
  }
}

// 加载所有用户列表（上传人）
const loadUsers = async () => {
  usersLoading.value = true
  try {
    const res = await api.users.list({ page: 1, size: 100 })
    users.value = res.data?.items || []
  } catch (error) {
    console.error('加载用户列表失败:', error)
  } finally {
    usersLoading.value = false
  }
}

// 加载图纸列表
const loadDrawings = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (searchForm.product_id) params.product_id = searchForm.product_id
    if (searchForm.project_group_id) params.project_group_id = searchForm.project_group_id
    if (searchForm.manager_id) params.manager_id = searchForm.manager_id
    if (searchForm.uploader_id) params.uploader_id = searchForm.uploader_id
    if (searchForm.creator_id) params.creator_id = searchForm.creator_id
    if (searchForm.confidentiality_level) params.confidentiality_level = searchForm.confidentiality_level
    if (searchForm.status && searchForm.status !== 'all') params.status = searchForm.status
    const res = await api.drawings.list(params)
    tableData.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    console.error('加载图纸列表失败:', error)
    ElMessage.error('加载图纸列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadProducts()
  loadProjectGroups()
  loadUsers()
  loadProjectLeaders()

  // 从 URL 读取筛选参数
  if (route.query.product_id) {
    searchForm.product_id = route.query.product_id
  }
  if (route.query.project_group_id) {
    searchForm.project_group_id = route.query.project_group_id
  }

  loadDrawings()
})

const getLevelLabel = (level) => {
  const map = { A: 'A 类 - 核心机密', B: 'B 类 - 重要', C: 'C 类 - 一般' }
  return map[level] || level
}

const getLevelTagType = (level) => {
  const map = { A: 'danger', B: 'warning', C: 'info' }
  return map[level] || 'info'
}

const getRowClassName = ({ row }) => {
  return row.status === 'archived' ? 'archived-row' : ''
}

const handleSearch = () => {
  pagination.page = 1
  loadDrawings()
}

const handleReset = () => {
  searchForm.keyword = ''
  searchForm.product_id = ''
  searchForm.project_group_id = ''
  searchForm.manager_id = ''
  searchForm.uploader_id = ''
  searchForm.creator_id = ''
  searchForm.confidentiality_level = ''
  searchForm.status = 'active'
  pagination.page = 1
  loadDrawings()
}

const handleCreate = () => {
  router.push('/drawings/create')
}

const handleExport = async () => {
  try {
    const params = {}
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (searchForm.product) params.product_id = searchForm.product
    if (searchForm.project_group) params.project_group_id = searchForm.project_group
    if (searchForm.manager) params.manager_id = searchForm.manager
    if (searchForm.uploader) params.uploader_id = searchForm.uploader
    if (searchForm.level) params.confidentiality_level = searchForm.level

    // 调用后端导出 API
    const res = await api.drawings.exportCsv(params)

    // 创建下载链接
    const blob = new Blob([res.data.content], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `drawings_export_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    ElMessage.success(`已导出 ${res.data.count} 条图纸数据`)
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败：' + error.message)
  }
}

const handleFullBackup = async () => {
  backupLoading.value = true
  try {
    const response = await fetch(`/api/drawings/export/backup`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })

    if (!response.ok) {
      throw new Error('备份失败')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `full_backup_${new Date().toISOString().split('T')[0]}.zip`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    ElMessage.success('全量备份下载成功')
  } catch (error) {
    console.error('备份失败:', error)
    ElMessage.error('全量备份失败：' + error.message)
  } finally {
    backupLoading.value = false
  }
}

const handleView = (row) => {
  router.push(`/drawings/${row.id}`)
}

const handleUpload = (row) => {
  router.push(`/drawings/${row.id}/upload`)
}

const handleDownload = (row) => {
  // 下载图纸文件
  const token = localStorage.getItem('token')
  const downloadUrl = `${api.drawings.download(row.id)}?token=${token}`

  // 创建下载链接
  const link = document.createElement('a')
  link.setAttribute('href', downloadUrl)
  link.setAttribute('download', '')
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const handleHistory = (row) => {
  router.push(`/drawings/${row.id}/history`)
}

const handleEdit = (row) => {
  router.push(`/drawings/${row.id}/edit`)
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认将图纸"${row.name}"作废吗？`, '提示', {
      type: 'warning'
    })
    await api.drawings.delete(row.id)
    ElMessage.success('图纸已作废')
    loadDrawings()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('作废失败：' + error.message)
    }
  }
}

const handleReactivate = async (row) => {
  try {
    await ElMessageBox.confirm(`确认重新激活图纸"${row.name}"吗？`, '提示', {
      type: 'warning'
    })
    await api.drawings.reactivate(row.id)
    ElMessage.success('图纸已重新激活')
    loadDrawings()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('重新激活失败：' + error.message)
    }
  }
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  loadDrawings()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadDrawings()
}
</script>

<style scoped>
.drawings-page {
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

.search-card {
  margin-bottom: 15px;
}

.search-form {
  display: flex;
  flex-wrap: wrap;
}

.table-card {
  min-height: 500px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

::v-deep .archived-row {
  background-color: #fef0f0 !important;
}
::v-deep .archived-row td {
  background-color: #fef0f0 !important;
}
::v-deep .el-table__row.archived-row {
  background-color: #fef0f0 !important;
}
</style>
