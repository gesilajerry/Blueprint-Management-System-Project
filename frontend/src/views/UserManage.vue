<template>
  <div class="user-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <div class="header-actions">
        <el-button @click="handleExport" style="margin-right: 10px">
          <el-icon><Download /></el-icon>
          导出
        </el-button>
        <el-button @click="showImportDialog = true" style="margin-right: 10px">
          <el-icon><Upload /></el-icon>
          导入
        </el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新增用户
        </el-button>
      </div>
    </div>

    <el-alert
      title="用户管理说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 15px"
    >
      <template #title>
        <div style="font-size: 13px">
          管理系统用户，分配角色和部门。
          <br>
          <span style="color: #909399; font-size: 12px">
            默认用户：admin(管理员)、zhangsan(设计师)、lishen(审定人)
          </span>
        </div>
      </template>
    </el-alert>

    <el-card class="table-card">
      <!-- 搜索区 -->
      <el-form :inline="true" class="search-form" style="margin-bottom: 15px">
        <el-form-item label="用户名/姓名">
          <el-input
            v-model="searchKeyword"
            placeholder="请输入用户名或姓名"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="所属部门">
          <el-select v-model="searchDept" placeholder="全部" clearable style="width: 150px">
            <el-option
              v-for="dept in deptList"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="searchRole" placeholder="全部" clearable style="width: 120px">
            <el-option
              v-for="role in roleList"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column label="所属部门" width="120">
          <template #default="{ row }">
            {{ getDeptLabel(row.department_id) }}
          </template>
        </el-table-column>
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role_id)" size="small">
              {{ getRoleLabel(row.role_id) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="手机" width="130" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
              {{ row.status === 'active' ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ row.created_at ? new Date(row.created_at).toLocaleDateString('zh-CN') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="handleResetPwd(row)">重置密码</el-button>
            <el-button
              link
              :type="row.status === 'active' ? 'warning' : 'success'"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 'active' ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          :current-page="pagination.page"
          :page-size="pagination.size"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'add' ? '新增用户' : '编辑用户'"
      width="600px"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username" required>
              <el-input
                v-model="formData.username"
                placeholder="登录用户名"
                maxlength="30"
                :disabled="dialogMode === 'edit'"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="name" required>
              <el-input v-model="formData.name" placeholder="真实姓名" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="所属部门" prop="department_id" required>
              <el-select v-model="formData.department_id" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="dept in deptList"
                  :key="dept.id"
                  :label="dept.name"
                  :value="dept.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="角色" prop="role_id" required>
              <el-select v-model="formData.role_id" placeholder="请选择" style="width: 100%">
                <el-option
                  v-for="role in roleList"
                  :key="role.id"
                  :label="role.name"
                  :value="role.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="formData.email" placeholder="example@company.com" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="手机" prop="phone">
              <el-input v-model="formData.phone" placeholder="11 位手机号" maxlength="11" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item
          v-if="dialogMode === 'add'"
          label="密码"
          prop="password"
          required
        >
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="初始密码（至少 6 位）"
            show-password
          />
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio value="active">正常</el-radio>
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

    <!-- 导入对话框 -->
    <el-dialog v-model="showImportDialog" title="批量导入用户" width="500px">
      <el-alert type="info" :closable="false" style="margin-bottom: 15px">
        <template #title>
          请上传 CSV 文件，表头需包含 <b>username</b>、<b>name</b>（必填），其他字段可选：email、phone、department_id、role_id、status。
          <br>
          导入用户的默认密码为 <b>123456</b>，首次登录后请自行修改。
        </template>
      </el-alert>
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        accept=".csv"
        :limit="1"
        :on-change="handleFileChange"
        style="text-align: center"
      >
        <el-icon><Upload /></el-icon>
        <div>拖拽 CSV 文件到此处，或 <em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">只能上传 CSV 文件</div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="handleImportConfirm" :loading="importing">
          确定导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus, Download, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../utils/api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const loading = ref(false)
const searchKeyword = ref('')
const searchDept = ref('')
const searchRole = ref('')
const dialogVisible = ref(false)
const dialogMode = ref('add')
const submitting = ref(false)
const formRef = ref(null)
const showImportDialog = ref(false)
const importing = ref(false)
const uploadRef = ref(null)
const selectedFile = ref(null)

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

// 部门列表
const deptList = ref([])
// 角色列表
const roleList = ref([])

// 表格数据
const tableData = ref([])

const formData = reactive({
  username: '',
  name: '',
  department_id: '',
  role_id: '',
  email: '',
  phone: '',
  password: '',
  status: 'active'
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  department_id: [{ required: true, message: '请选择所属部门', trigger: 'change' }],
  role_id: [{ required: true, message: '请选择角色', trigger: 'change' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, message: '密码至少 6 位', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确的邮箱', trigger: 'blur' }]
}

// 加载部门和角色列表
const loadDictData = async () => {
  try {
    const [deptRes, roleRes] = await Promise.all([
      api.departments.list({ page: 1, size: 100 }),
      api.roles.list({ page: 1, size: 100 })
    ])
    deptList.value = deptRes.data?.items || []
    roleList.value = roleRes.data?.items || []
  } catch (error) {
    console.error('加载字典数据失败:', error)
  }
}

// 加载用户列表
const loadUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size,
      keyword: searchKeyword.value || undefined,
      department_id: searchDept.value || undefined,
      role_id: searchRole.value || undefined
    }
    const res = await api.users.list(params)
    tableData.value = res.data?.items || []
    pagination.total = res.data?.total || 0
  } catch (error) {
    console.error('加载用户列表失败:', error)
    ElMessage.error('加载用户列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDictData()
  loadUsers()
})

const getRoleLabel = (roleId) => {
  const role = roleList.value.find(r => r.id === roleId)
  return role?.name || roleId
}

const getRoleTagType = (roleId) => {
  const role = roleList.value.find(r => r.id === roleId)
  const code = role?.code || ''
  const map = { role_admin: 'danger', role_designer: '', role_reviewer: 'warning', role_guest: 'info' }
  return map[code] || 'info'
}

const getDeptLabel = (deptId) => {
  const dept = deptList.value.find(d => d.id === deptId)
  return dept?.name || deptId
}

const handleSearch = () => {
  pagination.page = 1
  loadUsers()
}

const handleReset = () => {
  searchKeyword.value = ''
  searchDept.value = ''
  searchRole.value = ''
  pagination.page = 1
  loadUsers()
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  loadUsers()
}

const handleCurrentChange = (page) => {
  pagination.page = page
  loadUsers()
}

const handleExport = async () => {
  try {
    const blob = await api.users.export()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'users_export.csv'
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败：' + error.message)
  }
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
}

const handleImportConfirm = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择 CSV 文件')
    return
  }

  importing.value = true
  try {
    const result = await api.users.import(selectedFile.value)
    ElMessage.success(`导入完成：成功 ${result.data?.success_count || 0} 条，跳过 ${result.data?.skipped_count || 0} 条`)
    if (result.data?.errors && result.data.errors.length > 0) {
      ElMessage.warning(`部分错误：${result.data.errors.join('; ')}`)
    }
    showImportDialog.value = false
    selectedFile.value = null
    loadUsers()
  } catch (error) {
    ElMessage.error('导入失败：' + error.message)
  } finally {
    importing.value = false
  }
}

const handleAdd = () => {
  dialogMode.value = 'add'
  Object.assign(formData, { username: '', name: '', department_id: '', role_id: '', email: '', phone: '', password: '', status: 'active' })
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  dialogMode.value = 'edit'
  try {
    const res = await api.users.get(row.id)
    const user = res.data
    Object.assign(formData, {
      username: user.username,
      name: user.name,
      department_id: user.department_id,
      role_id: user.role_id,
      email: user.email,
      phone: user.phone,
      status: user.status
    })
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取用户详情失败：' + error.message)
  }
}

const handleResetPwd = (row) => {
  ElMessageBox.prompt('请输入新密码', '重置密码', {
    inputType: 'password',
    inputPattern: /.{6,}/,
    inputErrorMessage: '密码至少 6 位'
  }).then(async ({ value }) => {
    try {
      await api.users.update(row.id, { password: value })
      ElMessage.success('密码重置成功')
    } catch (error) {
      ElMessage.error('密码重置失败：' + error.message)
    }
  }).catch(() => {})
}

const handleToggleStatus = async (row) => {
  const newStatus = row.status === 'active' ? 'disabled' : 'active'
  const action = newStatus === 'active' ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(`确认${action}用户"${row.name}"吗？`, '提示', { type: 'warning' })
    await api.users.update(row.id, { status: newStatus })
    ElMessage.success(`${action}成功`)
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`${action}失败：` + error.message)
    }
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const data = {
          username: formData.username,
          name: formData.name,
          department_id: formData.department_id,
          role_id: formData.role_id,
          email: formData.email,
          phone: formData.phone,
          status: formData.status
        }

        if (dialogMode.value === 'add') {
          data.password = formData.password
          await api.users.create(data)
          ElMessage.success('新增成功')
        } else {
          await api.users.update(tableData.value.find(u => u.id === tableData.value.find(u => u.username === formData.username)?.id)?.id || '', data)
          ElMessage.success('更新成功')
        }

        dialogVisible.value = false
        loadUsers()
      } catch (error) {
        ElMessage.error((dialogMode.value === 'add' ? '新增' : '更新') + '失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
  })
}
</script>

<style scoped>
.user-page {
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
</style>
