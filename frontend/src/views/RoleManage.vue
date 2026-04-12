<template>
  <div class="role-page">
    <div class="page-header">
      <h2>角色权限管理</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增角色
      </el-button>
    </div>

    <el-alert
      title="角色权限说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 15px"
    >
      <template #title>
        <div style="font-size: 13px">
          系统预设 7 个角色：管理员、CTO、项目负责人、工程师、设计师、审定人、访客。
          <br>
          <span style="color: #909399; font-size: 12px">预设角色权限可调整，点击"恢复默认"可重置</span>
        </div>
      </template>
    </el-alert>

    <el-row :gutter="20">
      <!-- 角色列表 -->
      <el-col :span="10">
        <el-card class="role-card">
          <template #header>
            <span>角色列表</span>
          </template>

          <el-table :data="roleList" stripe highlight-current-row @current-change="handleRoleChange">
            <el-table-column prop="name" label="角色名称" />
            <el-table-column prop="code" label="角色编码" width="120">
              <template #default="{ row }">
                <el-tag v-if="isPresetRole(row.code)" type="primary" size="small">预设</el-tag>
                <span v-else>{{ row.code }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small">
                  {{ row.status === 'active' ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 权限配置 -->
      <el-col :span="14">
        <el-card class="permission-card">
          <template #header>
            <div class="card-header">
              <span>权限配置 - {{ selectedRole?.name }}</span>
              <div>
                <el-button
                  v-if="selectedRole && isPresetRole(selectedRole.code)"
                  size="small"
                  @click="handleRestoreDefault"
                  style="margin-right: 10px"
                >
                  恢复默认
                </el-button>
                <el-button type="primary" size="small" @click="handleSavePermission">保存配置</el-button>
              </div>
            </div>
          </template>

          <el-form label-width="120px">
            <el-form-item label="图纸查看">
              <el-checkbox v-model="permissions.viewAllDrawings">查看所有图纸</el-checkbox>
              <el-checkbox v-model="permissions.viewProjectDrawings">查看项目组图纸</el-checkbox>
              <el-checkbox v-model="permissions.viewOwnDrawings">查看自己创建的图纸</el-checkbox>
              <el-checkbox v-model="permissions.viewPendingReview">查看待审定图纸</el-checkbox>
              <el-checkbox v-model="permissions.viewAlevelDrawings">查看 A 类图纸</el-checkbox>
            </el-form-item>

            <el-form-item label="图纸操作">
              <el-checkbox v-model="permissions.createDrawing">创建图纸</el-checkbox>
              <el-checkbox v-model="permissions.uploadVersion">上传版本</el-checkbox>
              <el-checkbox v-model="permissions.downloadDrawing">下载图纸</el-checkbox>
            </el-form-item>

            <el-form-item label="保密审核">
              <el-checkbox v-model="permissions.reviewConfidentiality">保密审核</el-checkbox>
            </el-form-item>

            <el-form-item label="系统管理">
              <el-checkbox v-model="permissions.manageDepartments">部门管理</el-checkbox>
              <el-checkbox v-model="permissions.manageProducts">产品立项管理</el-checkbox>
              <el-checkbox v-model="permissions.manageProjectGroups">项目组管理</el-checkbox>
              <el-checkbox v-model="permissions.manageCoreParts">核心部件词库</el-checkbox>
              <el-checkbox v-model="permissions.manageUsers">用户管理</el-checkbox>
              <el-checkbox v-model="permissions.manageRoles">角色权限管理</el-checkbox>
            </el-form-item>

            <el-form-item label="其他">
              <el-checkbox v-model="permissions.viewDashboard">查看统计看板</el-checkbox>
              <el-checkbox v-model="permissions.viewLogs">查看系统日志</el-checkbox>
              <el-checkbox v-model="permissions.workLog">工作日志</el-checkbox>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 权限矩阵表格 -->
    <el-card class="matrix-card" style="margin-top: 20px">
      <template #header>
        <span>权限矩阵总览</span>
      </template>

      <el-table :data="permissionMatrix" stripe style="width: 100%" size="small">
        <el-table-column prop="feature" label="功能模块" min-width="180" />
        <el-table-column label="管理员" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.admin" type="success" size="small">✓</el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="CTO" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.cto" type="success" size="small">✓</el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="项目负责人" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.project_manager" type="success" size="small">✓</el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="工程师" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.engineer" type="success" size="small">✓</el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="设计师" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.designer" type="success" size="small">✓</el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="审定人" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.reviewer" type="success" size="small">✓</el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="档案管理员" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.archive_manager" type="success" size="small">✓</el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
        <el-table-column label="访客" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.guest" type="success" size="small">✓</el-tag>
            <span v-else style="color: #c0c4cc">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增角色对话框 -->
    <el-dialog
      v-model="addDialogVisible"
      title="新增角色"
      width="500px"
    >
      <el-form :model="newRole" label-width="100px">
        <el-form-item label="角色名称" required>
          <el-input v-model="newRole.name" placeholder="如：部门主管" />
        </el-form-item>
        <el-form-item label="角色编码" required>
          <el-input v-model="newRole.code" placeholder="如：dept_manager" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="newRole.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddRole">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '../utils/api'

const selectedRole = ref(null)

const roleList = ref([])

const permissions = reactive({
  // 图纸查看
  viewDashboard: false,
  viewDrawings: false,
  viewAllDrawings: false,
  viewProjectDrawings: false,
  viewOwnDrawings: false,
  viewPendingReview: false,
  viewAlevelDrawings: false,
  // 图纸操作
  createDrawing: false,
  uploadVersion: false,
  downloadDrawing: false,
  // 保密审核
  reviewConfidentiality: false,
  // 管理功能
  manageUsers: false,
  manageRoles: false,
  manageProjectGroups: false,
  manageDepartments: false,
  manageProducts: false,
  manageCoreParts: false,
  // 其他
  viewLogs: false,
  workLog: false
})

// 预设角色的默认权限（与后端 DEFAULT_ROLE_PERMISSIONS 一致）
const DEFAULT_PERMISSIONS = {
  admin: {
    viewDashboard: true,
    viewDrawings: true,
    viewAllDrawings: true,
    viewProjectDrawings: true,
    viewOwnDrawings: true,
    viewPendingReview: true,
    viewAlevelDrawings: true,
    createDrawing: true,
    uploadVersion: true,
    downloadDrawing: true,
    reviewConfidentiality: true,
    manageUsers: true,
    manageRoles: true,
    manageProjectGroups: true,
    manageDepartments: true,
    manageProducts: true,
    manageCoreParts: true,
    viewLogs: true,
    workLog: true
  },
  cto: {
    viewDashboard: true,
    viewDrawings: true,
    viewAllDrawings: true,
    viewProjectDrawings: true,
    viewOwnDrawings: false,
    viewPendingReview: true,
    viewAlevelDrawings: true,
    createDrawing: false,
    uploadVersion: false,
    downloadDrawing: false,
    reviewConfidentiality: true,
    manageUsers: false,
    manageRoles: false,
    manageProjectGroups: false,
    manageDepartments: false,
    manageProducts: false,
    manageCoreParts: false,
    viewLogs: true,
    workLog: true
  },
  project_manager: {
    viewDashboard: true,
    viewDrawings: true,
    viewAllDrawings: false,
    viewProjectDrawings: true,
    viewOwnDrawings: true,
    viewPendingReview: false,
    viewAlevelDrawings: false,
    createDrawing: true,
    uploadVersion: true,
    downloadDrawing: false,
    reviewConfidentiality: false,
    manageUsers: false,
    manageRoles: false,
    manageProjectGroups: false,
    manageDepartments: false,
    manageProducts: true,
    manageCoreParts: false,
    viewLogs: false,
    workLog: true
  },
  engineer: {
    viewDashboard: false,
    viewDrawings: true,
    viewAllDrawings: false,
    viewProjectDrawings: false,
    viewOwnDrawings: true,
    viewPendingReview: false,
    viewAlevelDrawings: false,
    createDrawing: true,
    uploadVersion: true,
    downloadDrawing: false,
    reviewConfidentiality: false,
    manageUsers: false,
    manageRoles: false,
    manageProjectGroups: false,
    manageDepartments: false,
    manageProducts: false,
    manageCoreParts: false,
    viewLogs: false,
    workLog: false
  },
  designer: {
    viewDashboard: false,
    viewDrawings: true,
    viewAllDrawings: false,
    viewProjectDrawings: false,
    viewOwnDrawings: true,
    viewPendingReview: false,
    viewAlevelDrawings: false,
    createDrawing: true,
    uploadVersion: true,
    downloadDrawing: false,
    reviewConfidentiality: false,
    manageUsers: false,
    manageRoles: false,
    manageProjectGroups: false,
    manageDepartments: false,
    manageProducts: false,
    manageCoreParts: false,
    viewLogs: false,
    workLog: false
  },
  reviewer: {
    viewDashboard: true,
    viewDrawings: true,
    viewAllDrawings: true,
    viewProjectDrawings: false,
    viewOwnDrawings: false,
    viewPendingReview: true,
    viewAlevelDrawings: false,
    createDrawing: true,
    uploadVersion: true,
    downloadDrawing: false,
    reviewConfidentiality: true,
    manageUsers: false,
    manageRoles: false,
    manageProjectGroups: false,
    manageDepartments: false,
    manageProducts: false,
    manageCoreParts: false,
    viewLogs: false,
    workLog: false
  },
  guest: {
    viewDashboard: false,
    viewDrawings: false,
    viewAllDrawings: false,
    viewProjectDrawings: false,
    viewOwnDrawings: false,
    viewPendingReview: false,
    viewAlevelDrawings: false,
    createDrawing: false,
    uploadVersion: false,
    downloadDrawing: false,
    reviewConfidentiality: false,
    manageUsers: false,
    manageRoles: false,
    manageProjectGroups: false,
    manageDepartments: false,
    manageProducts: false,
    manageCoreParts: false,
    viewLogs: false,
    workLog: false
  },
  archive_manager: {
    viewDashboard: true,
    viewDrawings: true,
    viewAllDrawings: true,
    viewProjectDrawings: true,
    viewOwnDrawings: false,
    viewPendingReview: false,
    viewAlevelDrawings: true,
    createDrawing: false,
    uploadVersion: false,
    downloadDrawing: true,
    reviewConfidentiality: false,
    manageUsers: false,
    manageRoles: false,
    manageProjectGroups: false,
    manageDepartments: false,
    manageProducts: false,
    manageCoreParts: false,
    viewLogs: true,
    workLog: true
  }
}

// 预设角色列表
const PRESET_ROLES = ['admin', 'cto', 'project_manager', 'engineer', 'designer', 'reviewer', 'archive_manager', 'guest']

const permissionMatrix = ref([
  { feature: '查看统计看板', admin: true, cto: true, project_manager: true, engineer: false, designer: false, reviewer: true, archive_manager: true, guest: false },
  { feature: '查看所有图纸', admin: true, cto: true, project_manager: false, engineer: false, designer: false, reviewer: true, archive_manager: true, guest: false },
  { feature: '查看项目组图纸', admin: true, cto: true, project_manager: true, engineer: false, designer: false, reviewer: false, archive_manager: true, guest: false },
  { feature: '查看自己图纸', admin: true, cto: false, project_manager: true, engineer: true, designer: true, reviewer: false, archive_manager: false, guest: false },
  { feature: '查看待审定图纸', admin: true, cto: true, project_manager: false, engineer: false, designer: false, reviewer: true, archive_manager: false, guest: false },
  { feature: '查看 A 类图纸', admin: true, cto: true, project_manager: false, engineer: false, designer: false, reviewer: false, archive_manager: true, guest: false },
  { feature: '创建图纸', admin: true, cto: false, project_manager: true, engineer: true, designer: true, reviewer: true, archive_manager: false, guest: false },
  { feature: '上传版本', admin: true, cto: false, project_manager: true, engineer: true, designer: true, reviewer: true, archive_manager: false, guest: false },
  { feature: '下载图纸', admin: true, cto: false, project_manager: false, engineer: false, designer: false, reviewer: false, archive_manager: true, guest: false },
  { feature: '保密审核', admin: true, cto: true, project_manager: false, engineer: false, designer: false, reviewer: true, archive_manager: false, guest: false },
  { feature: '用户管理', admin: true, cto: false, project_manager: false, engineer: false, designer: false, reviewer: false, archive_manager: false, guest: false },
  { feature: '角色权限管理', admin: true, cto: false, project_manager: false, engineer: false, designer: false, reviewer: false, archive_manager: false, guest: false },
  { feature: '项目组管理', admin: true, cto: false, project_manager: false, engineer: false, designer: false, reviewer: false, archive_manager: false, guest: false },
  { feature: '产品立项管理', admin: true, cto: false, project_manager: true, engineer: false, designer: false, reviewer: false, archive_manager: false, guest: false },
  { feature: '核心部件词库', admin: true, cto: false, project_manager: false, engineer: false, designer: false, reviewer: false, archive_manager: false, guest: false },
  { feature: '查看系统日志', admin: true, cto: true, project_manager: false, engineer: false, designer: false, reviewer: false, archive_manager: true, guest: false },
  { feature: '工作日志', admin: true, cto: true, project_manager: true, engineer: false, designer: false, reviewer: false, archive_manager: true, guest: false }
])

const addDialogVisible = ref(false)
const newRole = reactive({
  name: '',
  code: '',
  status: 'active'
})

// 检查是否是预设角色
const isPresetRole = (code) => {
  return PRESET_ROLES.includes(code)
}

// 加载角色列表
const loadRoles = async () => {
  try {
    const res = await api.roles.list({ page: 1, size: 20 })
    roleList.value = res.data?.items || []
    if (roleList.value.length > 0) {
      handleRoleChange(roleList.value[0])
    }
  } catch (error) {
    console.error('加载角色列表失败:', error)
  }
}

onMounted(() => {
  loadRoles()
})

const handleRoleChange = (row) => {
  if (!row) return

  selectedRole.value = row
  // 如果角色有已保存的权限，使用已保存的；否则使用默认权限
  if (row.permissions && Object.keys(row.permissions).length > 0) {
    Object.assign(permissions, row.permissions)
  } else {
    const defaults = DEFAULT_PERMISSIONS[row.code] || DEFAULT_PERMISSIONS['guest']
    Object.assign(permissions, defaults)
  }
}

const handleAdd = () => {
  addDialogVisible.value = true
}

const handleAddRole = async () => {
  if (!newRole.name || !newRole.code) {
    ElMessage.warning('请填写角色名称和编码')
    return
  }

  try {
    await api.roles.create({
      name: newRole.name,
      code: newRole.code,
      permissions: {},
      status: newRole.status
    })
    ElMessage.success('角色已添加')
    addDialogVisible.value = false
    // 重置表单
    newRole.name = ''
    newRole.code = ''
    newRole.status = 'active'
    // 重新加载角色列表
    loadRoles()
  } catch (error) {
    console.error('添加角色失败:', error)
    ElMessage.error('添加角色失败：' + error.message)
  }
}

const handleSavePermission = async () => {
  if (!selectedRole.value) {
    ElMessage.warning('请先选择一个角色')
    return
  }

  try {
    await api.roles.update(selectedRole.value.id, { permissions: { ...permissions } })
    ElMessage.success('权限配置已保存')
  } catch (error) {
    console.error('保存权限失败:', error)
    ElMessage.error('保存权限失败：' + error.message)
  }
}

const handleRestoreDefault = async () => {
  if (!selectedRole.value) return

  try {
    await ElMessageBox.confirm(
      `确认恢复角色"${selectedRole.value.name}"的默认权限吗？`,
      '恢复默认',
      { type: 'warning' }
    )

    const defaults = DEFAULT_PERMISSIONS[selectedRole.value.code] || DEFAULT_PERMISSIONS['guest']
    Object.assign(permissions, defaults)
    ElMessage.success('已恢复默认权限')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('恢复默认失败:', error)
    }
  }
}
</script>

<style scoped>
.role-page {
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

.role-card {
  min-height: 400px;
}

.permission-card {
  min-height: 400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.matrix-card {
  min-height: 400px;
}
</style>

