import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../utils/api'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('user') || '{}'))
  // 权限（从后端 /auth/me 获取）
  const permissions = ref(JSON.parse(localStorage.getItem('permissions') || '{}'))

  // 角色列表（用于显示）
  const roles = {
    admin: '管理员',
    cto: 'CTO',
    project_manager: '项目负责人',
    engineer: '工程师',
    designer: '设计师',
    reviewer: '审定人',
    archive_manager: '档案管理员',
    guest: '访客'
  }

  // 角色 ID 转角色码
  function getRoleCode(roleId) {
    const roleMap = {
      'role_admin': 'admin',
      'role_cto': 'cto',
      'role_project_manager': 'project_manager',
      'role_engineer': 'engineer',
      'role_designer': 'designer',
      'role_reviewer': 'reviewer',
      'role_archive_manager': 'archive_manager',
      'role_guest': 'guest'
    }
    return roleMap[roleId] || 'guest'
  }

  // 计算属性 - 当前用户角色
  const userRole = computed(() => {
    // 优先使用后端返回的 role_code
    if (userInfo.value?.role_code) {
      return userInfo.value.role_code
    }
    return userInfo.value?.role_id ? getRoleCode(userInfo.value.role_id) : 'guest'
  })

  // 计算属性 - 用户权限（从后端获取的优先）
  const userPermissions = computed(() => {
    return permissions.value || {}
  })

  // 从后端刷新用户信息和权限
  async function refreshUserInfo() {
    if (!token.value) return

    try {
      const res = await api.auth.me()
      const data = res.data

      // 更新本地存储
      userInfo.value = {
        id: data.id,
        username: data.username,
        name: data.name,
        email: data.email,
        phone: data.phone,
        department_id: data.department_id,
        role_id: data.role_id,
        role_code: data.role_code,
        status: data.status
      }

      permissions.value = data.permissions || {}

      localStorage.setItem('user', JSON.stringify(userInfo.value))
      localStorage.setItem('permissions', JSON.stringify(permissions.value))

      return data
    } catch (error) {
      console.error('刷新用户信息失败:', error)
      return null
    }
  }

  // 设置用户信息（登录时调用）
  function setUserInfo(user, userToken) {
    userInfo.value = user
    token.value = userToken
    localStorage.setItem('user', JSON.stringify(user))
    localStorage.setItem('token', userToken)

    // 如果后端返回了权限，保存它
    if (user.permissions) {
      permissions.value = user.permissions
      localStorage.setItem('permissions', JSON.stringify(user.permissions))
    }
  }

  // 清除用户信息
  function clearUserInfo() {
    userInfo.value = {}
    token.value = ''
    permissions.value = {}
    localStorage.removeItem('user')
    localStorage.removeItem('token')
    localStorage.removeItem('permissions')
  }

  // 检查权限
  function hasPermission(permission) {
    return userPermissions.value[permission] === true
  }

  // 检查是否是管理员
  function isAdmin() {
    return userRole.value === 'admin'
  }

  // 检查是否是审定人（可审核但不一定能编辑）
  function isReviewer() {
    return userRole.value === 'reviewer' || userRole.value === 'admin' || userRole.value === 'cto'
  }

  // 检查是否能编辑图纸（管理员/CTO/项目负责人/工程师/设计师可以，审定人/访客不行）
  function canEditDrawing() {
    const role = userRole.value
    return ['admin', 'cto', 'project_manager', 'engineer', 'designer'].includes(role)
  }

  // 是否已登录
  function isLoggedIn() {
    return !!token.value
  }

  return {
    // 状态
    token,
    userInfo,
    permissions,
    userRole,
    userPermissions,
    roles,
    // 方法
    getRoleCode,
    refreshUserInfo,
    setUserInfo,
    clearUserInfo,
    hasPermission,
    isAdmin,
    isReviewer,
    canEditDrawing,
    isLoggedIn
  }
})
