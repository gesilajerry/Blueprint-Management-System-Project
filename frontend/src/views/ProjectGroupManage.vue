<template>
  <div class="project-group-page">
    <div class="page-header">
      <h2>项目组管理</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增项目组
      </el-button>
    </div>

    <el-alert
      title="项目组说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 15px"
    >
      <template #title>
        <div style="font-size: 13px">
          项目组是研发工程部下的组织架构，一个项目组可以负责多个产品/项目。
          项目负责人可查看项目组内所有图纸，工程师仅可查看自己参与的图纸。
        </div>
      </template>
    </el-alert>

    <el-card class="table-card" v-loading="loading">
      <el-table :data="tableData" stripe style="width: 100%">
        <el-table-column prop="code" label="项目组编号" width="150" />
        <el-table-column prop="name" label="项目组名称" min-width="200" />
        <el-table-column prop="leader_name" label="项目负责人" width="120" />
        <el-table-column prop="member_count" label="成员数" width="80" />
        <el-table-column prop="product_count" label="产品数" width="80" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.created_at ? row.created_at.replace('T', ' ').substring(0, 16) : '' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">详情</el-button>
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button
              link
              :type="row.status === 'active' ? 'warning' : 'success'"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 'active' ? '禁用' : '启用' }}
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

    <!-- 详情对话框 -->
    <el-dialog
      v-model="viewDialogVisible"
      title="项目组详情"
      width="800px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="项目组编号">{{ currentGroup.code }}</el-descriptions-item>
        <el-descriptions-item label="项目组名称">{{ currentGroup.name }}</el-descriptions-item>
        <el-descriptions-item label="项目负责人">{{ currentGroup.leader_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentGroup.status === 'active' ? 'success' : 'info'">
            {{ currentGroup.status === 'active' ? '启用' : '禁用' }}
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <el-divider>项目组成员</el-divider>
      <el-table :data="currentGroup.members || []" stripe style="width: 100%">
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role_type === 'manager' ? 'warning' : 'info'">
              {{ row.role_type === 'manager' ? '项目负责人' : '工程师' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机" width="130" />
      </el-table>

      <el-divider>关联产品/项目</el-divider>
      <el-table :data="currentGroup.products || []" stripe style="width: 100%">
        <el-table-column prop="code" label="项目编号" width="150" />
        <el-table-column prop="name" label="项目名称" min-width="200" />
        <el-table-column prop="manager" label="负责人" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '进行中' : '已归档' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? '新增项目组' : '编辑项目组'"
      width="650px"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="项目组名称" prop="name" required>
          <el-input
            v-model="formData.name"
            placeholder="如：智能控制器项目组"
            maxlength="100"
          />
        </el-form-item>

        <el-form-item label="项目组编号" prop="code" required>
          <el-input
            v-model="formData.code"
            placeholder="如：PG-2024-001"
            maxlength="50"
            :disabled="dialogMode === 'edit'"
          />
          <div class="form-tip">项目组唯一标识，用于系统关联</div>
        </el-form-item>

        <el-form-item label="项目负责人" prop="leader_id" required>
          <el-select
            v-model="formData.leader_id"
            placeholder="请选择项目负责人"
            style="width: 100%"
            :loading="usersLoading"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.name"
              :value="user.id"
            />
          </el-select>
          <div class="form-tip">负责人将自动成为项目组成员（项目负责人角色）</div>
        </el-form-item>

        <el-form-item label="项目组成员" prop="member_ids">
          <el-select
            v-model="formData.member_ids"
            multiple
            placeholder="选择项目组成员（工程师）"
            style="width: 100%"
            :loading="usersLoading"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.name"
              :value="user.id"
              :disabled="user.id === formData.leader_id"
            />
          </el-select>
          <div class="form-tip">选中的成员将以工程师身份参与项目组，可上传和查看该项目组图纸</div>
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">禁用</el-radio>
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
import { api, postForm } from '../utils/api'

const loading = ref(false)
const usersLoading = ref(false)
const dialogVisible = ref(false)
const dialogMode = ref('add')
const viewDialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const tableData = ref([])
const currentGroup = reactive({
  id: '',
  code: '',
  name: '',
  leader_id: '',
  leader_name: '',
  status: 'active',
  members: [],
  products: []
})

const formData = reactive({
  id: '',
  name: '',
  code: '',
  leader_id: '',
  member_ids: [],
  status: 'active'
})

const users = ref([])

const rules = {
  name: [{ required: true, message: '请输入项目组名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入项目组编号', trigger: 'blur' }],
  leader_id: [{ required: true, message: '请选择项目负责人', trigger: 'change' }]
}

// 加载项目组列表
const loadProjectGroups = async () => {
  loading.value = true
  try {
    const res = await api.projectGroups.list({
      page: pagination.page,
      size: pagination.size
    })
    tableData.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    console.error('加载项目组列表失败:', error)
    ElMessage.error('加载项目组列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 加载用户列表
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

onMounted(() => {
  loadProjectGroups()
  loadUsers()
})

const handleAdd = () => {
  dialogMode.value = 'add'
  Object.assign(formData, {
    id: '',
    name: '',
    code: '',
    leader_id: '',
    member_ids: [],
    status: 'active'
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogMode.value = 'edit'
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    code: row.code,
    leader_id: row.leader_id,
    member_ids: row.members?.filter(m => m.role_type === 'engineer').map(m => m.id) || [],
    status: row.status
  })
  dialogVisible.value = true
}

const handleView = async (row) => {
  try {
    const res = await api.projectGroups.get(row.id)
    Object.assign(currentGroup, res.data)
    viewDialogVisible.value = true
  } catch (error) {
    console.error('加载项目组详情失败:', error)
    ElMessage.error('加载项目组详情失败：' + error.message)
  }
}

const handleToggleStatus = async (row) => {
  const newStatus = row.status === 'active' ? 'disabled' : 'active'
  const action = newStatus === 'active' ? '启用' : '禁用'

  try {
    await ElMessageBox.confirm(`确认${action}项目组"${row.name}"吗？`, '提示', { type: 'warning' })
    await api.projectGroups.update(row.id, { status: newStatus })
    ElMessage.success(`${action}成功`)
    loadProjectGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`${action}失败：` + error.message)
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除项目组"${row.name}"吗？`, '提示', { type: 'warning' })
    await api.projectGroups.delete(row.id)
    ElMessage.success('已删除')
    loadProjectGroups()
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
          leader_id: formData.leader_id,
          member_ids: formData.member_ids?.join(',') || ''
        }

        if (dialogMode.value === 'add') {
          await api.projectGroups.create(params)
          ElMessage.success('新增成功')
        } else {
          await api.projectGroups.update(formData.id, params)
          ElMessage.success('更新成功')
        }

        dialogVisible.value = false
        loadProjectGroups()
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
  loadProjectGroups()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadProjectGroups()
}
</script>

<style scoped>
.project-group-page {
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
