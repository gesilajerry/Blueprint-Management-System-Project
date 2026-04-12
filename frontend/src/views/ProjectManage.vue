<template>
  <div class="project-page">
    <div class="page-header">
      <h2>项目组字典管理</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增项目组
      </el-button>
    </div>

    <el-alert
      title="项目组字典说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 15px"
    >
      <template #title>
        <div style="font-size: 13px">
          用于图纸所属项目组选择和用户所属项目组分配。
        </div>
      </template>
    </el-alert>

    <el-card class="table-card">
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="code" label="项目组编码" width="150" />
        <el-table-column prop="name" label="项目组名称" min-width="200" />
        <el-table-column prop="manager" label="负责人" width="100" />
        <el-table-column prop="sort" label="排序" width="80" />
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
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
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

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? '新增项目组' : '编辑项目组'"
      width="550px"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="项目组名称" prop="name" required>
          <el-input
            v-model="formData.name"
            placeholder="如：智能控制器项目组"
            maxlength="50"
          />
        </el-form-item>

        <el-form-item label="项目组编码" prop="code" required>
          <el-input
            v-model="formData.code"
            placeholder="如：PROJ-001"
            maxlength="20"
            :disabled="dialogMode === 'edit'"
          />
          <div class="form-tip">项目组唯一标识，用于系统关联</div>
        </el-form-item>

        <el-form-item label="负责人">
          <el-input v-model="formData.manager" placeholder="项目组负责人姓名" />
        </el-form-item>

        <el-form-item label="排序" prop="sort">
          <el-input-number v-model="formData.sort" :min="0" :max="999" />
          <div class="form-tip">数字越小越靠前</div>
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
const dialogVisible = ref(false)
const dialogMode = ref('add')
const submitting = ref(false)
const formRef = ref(null)

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
  manager: '',
  sort: 1,
  status: 'active'
})

const rules = {
  name: [{ required: true, message: '请输入项目组名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入项目组编码', trigger: 'blur' }]
}

// 加载项目组列表
const loadProjects = async () => {
  loading.value = true
  try {
    const res = await api.departments.list({
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

onMounted(() => {
  loadProjects()
})

const handleAdd = () => {
  dialogMode.value = 'add'
  Object.assign(formData, { id: '', name: '', code: '', manager: '', sort: 1, status: 'active' })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogMode.value = 'edit'
  Object.assign(formData, {
    id: row.id,
    name: row.name,
    code: row.code,
    manager: row.manager,
    sort: row.sort,
    status: row.status
  })
  dialogVisible.value = true
}

const handleToggleStatus = async (row) => {
  const newStatus = row.status === 'active' ? 'disabled' : 'active'
  const action = newStatus === 'active' ? '启用' : '禁用'

  try {
    await ElMessageBox.confirm(`确认${action}项目组"${row.name}"吗？`, '提示', { type: 'warning' })
    await api.departments.update(row.id, { status: newStatus })
    ElMessage.success(`${action}成功`)
    loadProjects()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`${action}失败：` + error.message)
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除项目组"${row.name}"吗？`, '提示', { type: 'warning' })
    await api.departments.delete(row.id)
    ElMessage.success('已删除')
    loadProjects()
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
          sort: formData.sort || 0
        }
        if (formData.manager) params.manager = formData.manager

        if (dialogMode.value === 'add') {
          await postForm('/departments', params)
          ElMessage.success('新增成功')
        } else {
          await postForm(`/departments/${formData.id}`, params)
          ElMessage.success('更新成功')
        }

        dialogVisible.value = false
        loadProjects()
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
  loadProjects()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadProjects()
}
</script>

<style scoped>
.project-page {
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
