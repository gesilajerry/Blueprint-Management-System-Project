<template>
  <div class="product-page">
    <div class="page-header">
      <div class="header-left">
        <h2>产品/项目立项管理</h2>
        <el-select v-model="filterStatus" size="default" style="width: 120px; margin-left: 20px" @change="handleFilterChange">
          <el-option label="全部" value="" />
          <el-option label="进行中" value="active" />
          <el-option label="已归档" value="archived" />
        </el-select>
      </div>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增产品/项目
      </el-button>
    </div>

    <el-alert
      title="产品/项目立项说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 15px"
    >
      <template #title>
        <div style="font-size: 13px">
          用于管理具体产品和项目的立项信息。每个产品/项目必须关联到一个项目组。
          图号将根据产品/项目编号自动生成。
        </div>
      </template>
    </el-alert>

    <el-card class="table-card" v-loading="loading">
      <el-table :data="tableData" stripe style="width: 100%">
        <el-table-column prop="code" label="立项编号" width="150" />
        <el-table-column prop="name" label="产品/项目名称" min-width="250" />
        <el-table-column prop="manager" label="负责人" width="120" />
        <el-table-column prop="start_date" label="立项日期" width="120">
          <template #default="{ row }">
            {{ row.start_date || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '进行中' : '已归档' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.created_at ? row.created_at.replace('T', ' ').substring(0, 16) : '' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button
              link
              :type="row.status === 'active' ? 'warning' : 'success'"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 'active' ? '归档' : '激活' }}
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? '新增产品/项目' : '编辑产品/项目'"
      width="550px"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="产品/项目名称" prop="name" required>
          <el-input
            v-model="formData.name"
            placeholder="如：智能控制模块 V1"
            maxlength="200"
          />
        </el-form-item>

        <el-form-item label="立项编号" prop="code" required>
          <el-input
            v-model="formData.code"
            placeholder="如：PROJ-2024-001"
            maxlength="50"
            :disabled="dialogMode === 'edit'"
          />
          <div class="form-tip">立项编号唯一，图号将基于此编号生成</div>
        </el-form-item>

        <el-form-item label="所属项目组" prop="project_group_id" required>
          <el-select
            v-model="formData.project_group_id"
            placeholder="请选择所属项目组"
            style="width: 100%"
            :loading="projectGroupsLoading"
            @change="handleProjectGroupChange"
          >
            <el-option
              v-for="pg in projectGroups"
              :key="pg.id"
              :label="pg.name"
              :value="pg.id"
            />
          </el-select>
          <div class="form-tip">产品/项目必须关联到一个项目组</div>
        </el-form-item>

        <el-form-item label="项目负责人" prop="manager_id">
          <el-select
            v-model="formData.manager_id"
            placeholder="请先选择项目组"
            style="width: 100%"
            :loading="membersLoading"
            clearable
          >
            <el-option
              v-for="member in projectGroupMembers"
              :key="member.id"
              :label="member.name"
              :value="member.id"
            >
              <span>{{ member.name }}</span>
              <span style="color: #909399; font-size: 12px; margin-left: 8px">
                {{ member.role_type === 'manager' ? '（项目负责人）' : '（工程师）' }}
              </span>
            </el-option>
          </el-select>
          <div class="form-tip">从项目组成员中选择负责人</div>
        </el-form-item>

        <el-form-item label="立项日期" prop="start_date">
          <el-date-picker
            v-model="formData.start_date"
            type="date"
            placeholder="选择立项日期"
            style="width: 100%"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio value="active">进行中</el-radio>
            <el-radio value="archived">已归档</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, postForm, putForm } from '../utils/api'

const loading = ref(false)
const projectGroupsLoading = ref(false)
const membersLoading = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('add')
const submitting = ref(false)
const formRef = ref(null)
const filterStatus = ref('')

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const tableData = ref([])

const formData = reactive({
  id: '',
  name: '',
  code: '',
  project_group_id: '',
  manager_id: '',
  start_date: '',
  status: 'active'
})

const projectGroups = ref([])
const projectGroupMembers = ref([])

const rules = {
  name: [{ required: true, message: '请输入产品/项目名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入立项编号', trigger: 'blur' }],
  project_group_id: [{ required: true, message: '请选择所属项目组', trigger: 'change' }]
}

// 加载产品列表
const loadProducts = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    if (filterStatus.value) {
      params.status = filterStatus.value
    }
    const res = await api.products.list(params)
    tableData.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    console.error('加载产品列表失败:', error)
    ElMessage.error('加载产品列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 加载项目组列表
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

// 加载项目组成员
const loadProjectGroupMembers = async (groupId) => {
  if (!groupId) {
    projectGroupMembers.value = []
    return
  }
  membersLoading.value = true
  try {
    const res = await api.projectGroups.get(groupId)
    projectGroupMembers.value = res.data?.members || []
  } catch (error) {
    console.error('加载项目组成员失败:', error)
    projectGroupMembers.value = []
  } finally {
    membersLoading.value = false
  }
}

// 项目组选择变化时加载成员
const handleProjectGroupChange = (groupId) => {
  formData.manager_id = '' // 清空之前的选择
  loadProjectGroupMembers(groupId)
}

onMounted(() => {
  loadProducts()
  loadProjectGroups()
})

const handleAdd = () => {
  dialogMode.value = 'add'
  Object.assign(formData, {
    id: '',
    name: '',
    code: '',
    project_group_id: '',
    manager_id: '',
    start_date: '',
    status: 'active'
  })
  projectGroupMembers.value = []
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  dialogMode.value = 'edit'
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    code: row.code,
    project_group_id: row.project_group_id,
    manager_id: row.manager_id || '',
    start_date: row.start_date,
    status: row.status
  })
  // 加载项目组成员
  await loadProjectGroupMembers(row.project_group_id)
  dialogVisible.value = true
}

const handleToggleStatus = async (row) => {
  const newStatus = row.status === 'active' ? 'archived' : 'active'
  const action = newStatus === 'active' ? '激活' : '归档'

  try {
    await ElMessageBox.confirm(`确认${action}项目"${row.name}"吗？`, '提示', { type: 'warning' })
    await api.products.update(row.id, { status: newStatus })
    ElMessage.success(`${action}成功`)
    loadProducts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`${action}失败：` + error.message)
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除项目"${row.name}"吗？`, '提示', { type: 'warning' })
    await api.products.delete(row.id)
    ElMessage.success('已删除')
    loadProducts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + error.message)
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const params = {
          name: formData.name,
          code: formData.code,
          project_group_id: formData.project_group_id,
          status: formData.status
        }
        if (formData.manager_id) params.manager_id = formData.manager_id
        if (formData.start_date) params.start_date = formData.start_date

        if (dialogMode.value === 'add') {
          await api.products.create(params)
          ElMessage.success('新增成功')
        } else {
          await api.products.update(formData.id, params)
          ElMessage.success('更新成功')
        }

        dialogVisible.value = false
        loadProducts()
      } catch (error) {
        console.error('提交失败:', error)
        ElMessage.error('提交失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
  })
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  loadProducts()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadProducts()
}

const handleFilterChange = () => {
  pagination.page = 1
  loadProducts()
}
</script>

<style scoped>
.product-page {
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

.header-left {
  display: flex;
  align-items: center;
}

.table-card {
  min-height: 400px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
