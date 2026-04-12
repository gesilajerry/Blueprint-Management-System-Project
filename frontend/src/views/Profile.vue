<template>
  <div class="profile-page">
    <div class="page-header">
      <h2>个人中心</h2>
    </div>

    <el-row :gutter="20">
      <!-- 左侧栏 -->
      <el-col :span="8">
        <!-- 个人信息卡片 -->
        <el-card class="profile-card">
          <div class="profile-avatar" @click="showAvatarDialog = true">
            <div class="avatar-display" :style="{ backgroundColor: avatarConfig.bgColor }">
              <span class="avatar-text">{{ getAvatarText() }}</span>
            </div>
            <el-icon class="avatar-edit-icon"><Edit /></el-icon>
          </div>
          <div class="profile-name">
            <h3>{{ userInfo.name || userInfo.username }}</h3>
            <el-tag :type="getRoleTagType(userInfo.role_id)" size="small">
              {{ getRoleLabel(userInfo.role_id) }}
            </el-tag>
          </div>
          <div class="profile-dept">
            {{ getDeptLabel(userInfo.department_id) }}
          </div>
        </el-card>

        <!-- 所在项目组 -->
        <el-card class="project-groups-card" style="margin-top: 15px">
          <template #header>
            <span>所在项目组</span>
          </template>
          <div v-if="projectGroupsLoading" style="text-align: center; padding: 20px">
            <el-icon class="is-loading"><Loading /></el-icon>
          </div>
          <div v-else-if="projectGroups.length === 0" style="text-align: center; padding: 20px; color: #909399">
            暂未加入任何项目组
          </div>
          <div v-else>
            <div v-for="pg in projectGroups" :key="pg.id" class="project-group-item">
              <div class="project-group-header">
                <span class="project-group-name">{{ pg.name }}</span>
                <el-tag :type="pg.role_type === 'manager' ? 'warning' : 'success'" size="small">
                  {{ pg.role_label }}
                </el-tag>
              </div>
              <div class="project-group-code">{{ pg.code }}</div>
              <div class="project-group-products" v-if="pg.products && pg.products.length > 0">
                <span class="products-label">所属产品/项目：</span>
                <el-tag
                  v-for="product in pg.products"
                  :key="product.id"
                  size="small"
                  style="margin-right: 5px; margin-bottom: 3px"
                >
                  {{ product.name }} ({{ product.code }})
                </el-tag>
              </div>
              <div v-else class="project-group-products">
                <span class="products-label">所属产品/项目：</span>
                <span style="color: #c0c4cc">暂无</span>
              </div>
              <el-divider style="margin: 10px 0" />
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧栏 -->
      <el-col :span="16">
        <el-card class="info-card">
          <template #header>
            <span>基本信息</span>
          </template>
          <el-form :model="userInfoForm" label-width="100px" label-position="left">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="用户名">
                  <el-input v-model="userInfoForm.username" disabled />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="姓名">
                  <el-input v-model="userInfoForm.name" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="邮箱">
                  <el-input v-model="userInfoForm.email" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="手机">
                  <el-input v-model="userInfoForm.phone" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item>
              <el-button type="primary" @click="handleUpdateProfile" :loading="updating">
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 修改密码 -->
        <el-card class="password-card" style="margin-top: 15px">
          <template #header>
            <span>修改密码</span>
          </template>
          <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px" label-position="left">
            <el-form-item label="当前密码" prop="oldPassword" required>
              <el-input
                v-model="passwordForm.oldPassword"
                type="password"
                placeholder="请输入当前密码"
                show-password
              />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword" required>
              <el-input
                v-model="passwordForm.newPassword"
                type="password"
                placeholder="请输入新密码（至少 6 位）"
                show-password
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword" required>
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                placeholder="请再次输入新密码"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button type="warning" @click="handleChangePassword" :loading="changingPwd">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <!-- 头像选择对话框 -->
    <el-dialog v-model="showAvatarDialog" title="选择头像" width="400px">
      <div class="avatar-grid">
        <div
          v-for="color in avatarColors"
          :key="color"
          class="avatar-option"
          :class="{ selected: avatarConfig.bgColor === color }"
          @click="selectAvatar(color)"
        >
          <div class="avatar-preview" :style="{ backgroundColor: color }">
            <span class="avatar-text">{{ getAvatarText() }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showAvatarDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmAvatar">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Edit } from '@element-plus/icons-vue'
import { api } from '../utils/api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const passwordFormRef = ref(null)
const updating = ref(false)
const changingPwd = ref(false)
const projectGroupsLoading = ref(false)
const projectGroups = ref([])
const showAvatarDialog = ref(false)

// 头像颜色选项
const avatarColors = [
  '#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399',
  '#C71585', '#00CED1', '#FF6347', '#4169E1', '#32CD32',
  '#FF69B4', '#1E90FF', '#FFD700', '#FF4500', '#9370DB'
]

// 头像配置
const avatarConfig = reactive({
  bgColor: '#409EFF'
})

const getAvatarText = () => {
  const name = userInfo.value?.name || userInfo.value?.username || '用户'
  if (name.length <= 2) return name
  return name.substring(0, 2)
}

const selectAvatar = (color) => {
  avatarConfig.bgColor = color
}

const confirmAvatar = () => {
  // 保存到本地存储
  localStorage.setItem('avatarConfig', JSON.stringify(avatarConfig))
  showAvatarDialog.value = false
  ElMessage.success('头像已更新')
}

const loadAvatarConfig = () => {
  const saved = localStorage.getItem('avatarConfig')
  if (saved) {
    try {
      Object.assign(avatarConfig, JSON.parse(saved))
    } catch (e) {
      console.error('加载头像配置失败', e)
    }
  }
}

const userInfo = ref({
  id: '',
  username: '',
  name: '',
  email: '',
  phone: '',
  department_id: '',
  role_id: ''
})

const userInfoForm = reactive({
  username: '',
  name: '',
  email: '',
  phone: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 加载用户信息
const loadUserInfo = async () => {
  try {
    const res = await api.auth.me()
    userInfo.value = res.data
    Object.assign(userInfoForm, {
      username: res.data.username,
      name: res.data.name,
      email: res.data.email,
      phone: res.data.phone
    })
  } catch (error) {
    console.error('加载用户信息失败:', error)
    ElMessage.error('加载用户信息失败：' + error.message)
  }
}

const getRoleLabel = (roleId) => {
  const map = {
    role_admin: '管理员',
    role_cto: 'CTO',
    role_project_manager: '项目负责人',
    role_engineer: '工程师',
    role_designer: '设计师',
    role_reviewer: '审定人',
    role_archive_manager: '档案管理员',
    role_guest: '访客'
  }
  return map[roleId] || roleId
}

const getRoleTagType = (roleId) => {
  const map = {
    role_admin: 'danger',
    role_cto: 'warning',
    role_project_manager: 'success',
    role_engineer: '',
    role_designer: '',
    role_reviewer: 'warning',
    role_archive_manager: 'info',
    role_guest: 'info'
  }
  return map[roleId] || 'info'
}

const getDeptLabel = (deptId) => {
  // 这里可以加载部门列表来显示部门名称
  return deptId || '未知部门'
}

// 加载所在项目组
const loadProjectGroups = async () => {
  projectGroupsLoading.value = true
  try {
    const res = await api.users.getMyProjectGroups()
    projectGroups.value = res.data || []
  } catch (error) {
    console.error('加载项目组失败:', error)
  } finally {
    projectGroupsLoading.value = false
  }
}

const handleUpdateProfile = async () => {
  updating.value = true
  try {
    await api.users.update(userInfo.value.id, {
      name: userInfoForm.name,
      email: userInfoForm.email,
      phone: userInfoForm.phone
    })
    ElMessage.success('个人信息更新成功')
    // 更新 store 中的用户信息
    userStore.setUserInfo({
      ...userStore.userInfo,
      name: userInfoForm.name,
      email: userInfoForm.email,
      phone: userInfoForm.phone
    }, userStore.token)
  } catch (error) {
    ElMessage.error('更新失败：' + error.message)
  } finally {
    updating.value = false
  }
}

const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      changingPwd.value = true
      try {
        // 先验证当前密码（通过登录验证）
        const loginRes = await api.auth.login(userInfo.value.username, passwordForm.oldPassword)
        if (loginRes.code === 200) {
          // 当前密码正确，执行修改密码
          await api.users.update(userInfo.value.id, {
            password: passwordForm.newPassword
          })
          ElMessage.success('密码修改成功，请重新登录')
          passwordForm.oldPassword = ''
          passwordForm.newPassword = ''
          passwordForm.confirmPassword = ''
          setTimeout(() => {
            userStore.clearUserInfo()
            window.location.href = '/login'
          }, 1500)
        }
      } catch (error) {
        if (error.message.includes('401')) {
          ElMessage.error('当前密码错误')
        } else {
          ElMessage.error('修改密码失败：' + error.message)
        }
      } finally {
        changingPwd.value = false
      }
    }
  })
}

onMounted(() => {
  loadUserInfo()
  loadProjectGroups()
  loadAvatarConfig()
})
</script>

<style scoped>
.profile-page {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.profile-card {
  text-align: center;
  min-height: 200px;
}

.profile-avatar {
  margin-bottom: 20px;
}

.profile-name h3 {
  margin: 10px 0;
  font-size: 20px;
  color: #303133;
}

.profile-dept {
  color: #909399;
  font-size: 14px;
}

.project-groups-card {
  min-height: 200px;
}

.project-group-item {
  padding: 5px 0;
}

.project-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.project-group-name {
  font-weight: bold;
  color: #303133;
}

.project-group-code {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.project-group-products {
  font-size: 13px;
  color: #606266;
}

.products-label {
  color: #909399;
}

.info-card,
.password-card {
  min-height: 300px;
}

.profile-avatar {
  position: relative;
  display: inline-block;
  cursor: pointer;
}

.avatar-display {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.avatar-text {
  color: white;
  font-size: 32px;
  font-weight: bold;
  text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
}

.avatar-edit-icon {
  position: absolute;
  bottom: 0;
  right: 0;
  background: #409EFF;
  color: white;
  border-radius: 50%;
  padding: 5px;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.3s;
}

.profile-avatar:hover .avatar-edit-icon {
  opacity: 1;
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
  padding: 10px;
  overflow: hidden;
}

.avatar-option {
  cursor: pointer;
  border: 3px solid transparent;
  border-radius: 50%;
  transition: all 0.3s;
}

.avatar-option:hover {
  transform: scale(1.1);
}

.avatar-option.selected {
  border-color: #409EFF;
}

.avatar-preview {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
}

.avatar-preview .avatar-text {
  font-size: 20px;
}
</style>
