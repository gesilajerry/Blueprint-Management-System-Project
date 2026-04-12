<template>
  <div class="products-page">
    <div class="page-header">
      <h2>产品/项目字典管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增产品
        </el-button>
      </div>
    </div>

    <el-alert
      title="产品字典说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 15px"
    >
      <template #title>
        <div style="font-size: 13px">
          用于图纸所属产品/项目选择和图号自动生成。
          <strong>立项编号（code）将作为图号前缀</strong>，如 PROJ-2024-001-0001-V1.0
          <br>
        </div>
      </template>
    </el-alert>

    <el-card class="table-card">
      <!-- 搜索区 -->
      <el-form :inline="true" class="search-form" style="margin-bottom: 15px">
        <el-form-item label="产品名称/编号">
          <el-input
            v-model="searchKeyword"
            placeholder="请输入产品名称或编号"
            clearable
            style="width: 250px"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchStatus" placeholder="全部" clearable style="width: 120px">
            <el-option label="进行中" value="active" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="code" label="立项编号" width="180" />
        <el-table-column prop="name" label="产品/项目名称" min-width="250" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '进行中' : '已归档' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department_name" label="所属部门" width="120" />
        <el-table-column prop="manager" label="负责人" width="100" />
        <el-table-column prop="start_date" label="立项日期" width="120" />
        <el-table-column prop="drawing_count" label="图纸数量" width="100" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button
              link
              :type="row.status === 'active' ? 'warning' : 'success'"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 'active' ? '归档' : '启用' }}
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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
      width="600px"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="立项编号" prop="code" required>
          <el-input
            v-model="formData.code"
            placeholder="如：PROJ-2024-001"
            maxlength="50"
            :disabled="dialogMode === 'edit'"
          />
          <div class="form-tip">
            图号前缀，如 PROJ-2024-001-0001-V1.0
          </div>
        </el-form-item>

        <el-form-item label="产品/项目名称" prop="name" required>
          <el-input
            v-model="formData.name"
            placeholder="如：智能控制模块 V1"
            maxlength="200"
          />
        </el-form-item>

        <el-form-item label="所属部门" prop="department_id" required>
          <el-select v-model="formData.department_id" placeholder="请选择" style="width: 100%">
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="负责人" prop="manager">
          <el-input v-model="formData.manager" placeholder="项目负责人姓名" />
        </el-form-item>

        <el-form-item label="立项日期" prop="start_date">
          <el-date-picker
            v-model="formData.start_date"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
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
import { Plus, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, postForm } from '../utils/api'

const loading = ref(false)
const submitting = ref(false)
const searchKeyword = ref('')
const searchStatus = ref('')
const dialogVisible = ref(false)
const dialogMode = ref('add')
const formRef = ref(null)
const departments = ref([])

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const tableData = ref([])

const formData = reactive({
  id: '',
  code: '',
  name: '',
  department_id: '',
  manager: '',
  start_date: '',
  status: 'active'
})

const rules = {
  code: [{ required: true, message: '请输入立项编号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入产品/项目名称', trigger: 'blur' }],
  department_id: [{ required: true, message: '请选择所属部门', trigger: 'change' }]
}

// 加载部门列表
const loadDepartments = async () => {
  try {
    const res = await api.departments.list({ page: 1, size: 100 })
    departments.value = res.data?.items || []
  } catch (error) {
    console.error('加载部门列表失败:', error)
  }
}

// 加载产品列表
const loadProducts = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (searchStatus.value) params.status = searchStatus.value

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

onMounted(() => {
  loadDepartments()
  loadProducts()
})

const handleSearch = () => {
  pagination.page = 1
  loadProducts()
}

const handleReset = () => {
  searchKeyword.value = ''
  searchStatus.value = ''
  pagination.page = 1
  loadProducts()
}

const handleAdd = () => {
  dialogMode.value = 'add'
  Object.assign(formData, {
    id: '',
    code: '',
    name: '',
    department_id: '',
    manager: '',
    start_date: '',
    status: 'active'
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogMode.value = 'edit'
  Object.assign(formData, {
    id: row.id,
    code: row.code,
    name: row.name,
    department_id: row.department_id,
    manager: row.manager,
    start_date: row.start_date,
    status: row.status
  })
  dialogVisible.value = true
}

const handleToggleStatus = async (row) => {
  const newStatus = row.status === 'active' ? 'archived' : 'active'
  const action = newStatus === 'active' ? '启用' : '归档'

  try {
    await ElMessageBox.confirm(`确认将"${row.name}"${action}吗？`, '提示', {
      type: 'warning'
    })

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
  if (row.drawing_count > 0) {
    ElMessage.warning('该项目下存在图纸，无法删除')
    return
  }

  try {
    await ElMessageBox.confirm(`确认删除"${row.name}"吗？`, '提示', {
      type: 'warning'
    })

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
          code: formData.code
        }
        if (formData.department_id) params.department_id = formData.department_id
        if (formData.manager) params.manager = formData.manager
        if (formData.start_date) params.start_date = formData.start_date

        if (dialogMode.value === 'add') {
          await postForm('/products', params)
          ElMessage.success('新增成功')
        } else {
          await postForm(`/products/${formData.id}`, params)
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
</script>

<style scoped>
.products-page {
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

.header-actions {
  display: flex;
  gap: 10px;
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
