import { createRouter, createWebHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { public: true }
  },
  {
    path: '/',
    component: () => import('../components/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { permission: 'viewDashboard' }
      },
      {
        path: 'drawings',
        name: 'DrawingsList',
        component: () => import('../views/DrawingsList.vue'),
        meta: { permission: 'viewDrawings' }
      },
      {
        path: 'drawings/create',
        name: 'DrawingsCreate',
        component: () => import('../views/DrawingsCreate.vue'),
        meta: { permission: 'createDrawing' }
      },
      {
        path: 'drawings/:id',
        name: 'DrawingsDetail',
        component: () => import('../views/DrawingsDetail.vue'),
        meta: { permission: 'viewDrawings' }
      },
      {
        path: 'drawings/:id/upload',
        name: 'DrawingsUpload',
        component: () => import('../views/DrawingsUpload.vue'),
        meta: { permission: 'uploadVersion' }
      },
      {
        path: 'drawings/:id/history',
        name: 'VersionHistory',
        component: () => import('../views/VersionHistory.vue'),
        meta: { permission: 'viewDrawings' }
      },
      {
        path: 'review',
        name: 'ReviewPage',
        component: () => import('../views/ReviewPage.vue'),
        meta: { permission: 'reviewConfidentiality' }
      },
      {
        path: 'core-parts',
        name: 'CorePartsManage',
        component: () => import('../views/CorePartsManage.vue'),
        meta: { permission: 'manageCoreParts' }
      },
      {
        path: 'products',
        name: 'ProductsManage',
        component: () => import('../views/ProductManage.vue'),
        meta: { permission: 'manageProducts' }
      },
      {
        path: 'project-groups',
        name: 'ProjectGroupManage',
        component: () => import('../views/ProjectGroupManage.vue'),
        meta: { permission: 'manageProjectGroups' }
      },
      {
        path: 'users',
        name: 'UserManage',
        component: () => import('../views/UserManage.vue'),
        meta: { permission: 'manageUsers' }
      },
      {
        path: 'roles',
        name: 'RoleManage',
        component: () => import('../views/RoleManage.vue'),
        meta: { permission: 'manageRoles' }
      },
      {
        path: 'logs',
        name: 'SystemLogs',
        component: () => import('../views/SystemLogs.vue'),
        meta: { permission: 'viewLogs' }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/Profile.vue')
      },
      {
        path: 'workload',
        name: 'WorkloadStats',
        component: () => import('../views/WorkloadStats.vue'),
        meta: { permission: 'viewDashboard' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 公开路由直接放行
  if (to.meta.public) {
    return next()
  }

  // 需要登录的路由
  if (!userStore.isLoggedIn()) {
    return next('/login')
  }

  // 检查权限是否已加载
  const userPermissions = userStore.userPermissions
  const hasLoadedPermissions = userPermissions && Object.keys(userPermissions).length > 0

  // 如果权限尚未加载且目标是需要权限的页面，先允许导航
  // 组件内会处理权限不足的显示
  if (to.meta.permission && !hasLoadedPermissions) {
    // 权限还没加载（可能是页面刷新后首次加载），直接放行
    // refreshUserInfo 会自动在后台更新权限
    return next()
  }

  // 需要权限的路由
  if (to.meta.permission) {
    if (!userStore.hasPermission(to.meta.permission)) {
      // 无权限，检查是否有其他可访问的页面
      if (to.path === '/dashboard' || to.path === '/') {
        if (userStore.hasPermission('viewDrawings')) {
          return next('/drawings')
        }
      }
      // 都没有权限，去 profile
      ElMessage.error('您没有权限访问该页面')
      return next('/profile')
    }
  }

  next()
})

export default router
