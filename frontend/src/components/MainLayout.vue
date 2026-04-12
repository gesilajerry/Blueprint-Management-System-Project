<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="side-bar">
      <div class="logo">
        <div class="logo-text-container" v-if="!isCollapse">
          <span class="logo-text">图纸管理系统</span>
          <img src="/logo.png" alt="Logo" class="logo-img" />
        </div>
        <span class="logo-text-short" v-else>BMS</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        :collapse="isCollapse"
        router
      >
        <el-menu-item index="/dashboard" v-if="userStore.hasPermission('viewDashboard')">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>统计看板</template>
        </el-menu-item>

        <el-menu-item index="/workload">
          <el-icon><TrendCharts /></el-icon>
          <template #title>工作量统计</template>
        </el-menu-item>

        <el-menu-item index="/drawings">
          <el-icon><Document /></el-icon>
          <template #title>图纸管理</template>
        </el-menu-item>

        <el-menu-item index="/review" v-if="userStore.hasPermission('reviewConfidentiality')">
          <el-icon><Checked /></el-icon>
          <template #title>保密审核</template>
        </el-menu-item>

        <el-sub-menu index="system">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/users" v-if="userStore.hasPermission('manageUsers')">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/roles" v-if="userStore.hasPermission('manageRoles')">
            <el-icon><UserFilled /></el-icon>
            <span>角色权限</span>
          </el-menu-item>
          <el-menu-item index="/project-groups" v-if="userStore.hasPermission('manageProjectGroups')">
            <el-icon><OfficeBuilding /></el-icon>
            <span>项目组管理</span>
          </el-menu-item>
          <el-menu-item index="/products" v-if="userStore.hasPermission('manageProducts')">
            <el-icon><List /></el-icon>
            <span>产品/项目立项</span>
          </el-menu-item>
          <el-menu-item index="/core-parts" v-if="userStore.hasPermission('manageCoreParts')">
            <el-icon><Key /></el-icon>
            <span>核心部件词库</span>
          </el-menu-item>
          <el-menu-item index="/logs" v-if="userStore.hasPermission('viewLogs')">
            <el-icon><Document /></el-icon>
            <span>系统日志</span>
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 顶栏 -->
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-icon" @click="toggleCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
        </div>

        <div class="header-right">
          <el-dropdown>
            <div class="user-info">
              <div class="user-avatar" :style="{ backgroundColor: avatarConfig.bgColor }">
                {{ getAvatarText() }}
              </div>
              <span class="username">{{ userStore.userInfo?.name || userStore.userInfo?.username || '用户' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleProfile">个人中心</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import {
  DataAnalysis, Document, Checked, Setting, Key, List, User, UserFilled, OfficeBuilding,
  Fold, Expand, ArrowDown, TrendCharts
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const isCollapse = ref(false)

const activeMenu = computed(() => route.path)

// 头像配置（与 Profile 页面同步）
const avatarConfig = ref({ bgColor: '#409EFF' })

const getAvatarText = () => {
  const name = userStore.userInfo?.name || userStore.userInfo?.username || '用户'
  if (name.length <= 2) return name
  return name.substring(0, 2)
}

const loadAvatarConfig = () => {
  const saved = localStorage.getItem('avatarConfig')
  if (saved) {
    try {
      avatarConfig.value = JSON.parse(saved)
    } catch (e) {
      console.error('加载头像配置失败', e)
    }
  }
}

loadAvatarConfig()

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const handleProfile = () => {
  router.push('/profile')
}

const handleLogout = () => {
  userStore.clearUserInfo()
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.side-bar {
  background-color: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background-color: #2b3a4b;
  gap: 8px;
  padding: 10px 0;
}

.logo-text-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.logo-text {
  white-space: nowrap;
  font-size: 16px;
}

.logo-img {
  height: 35px;
  width: auto;
  max-width: 100%;
}

.logo-text-short {
  font-size: 16px;
}

.el-menu {
  border-right: none;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.collapse-icon {
  font-size: 20px;
  cursor: pointer;
  color: #606266;
}

.collapse-icon:hover {
  color: #409EFF;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  font-weight: bold;
}

.username {
  color: #606266;
  font-size: 14px;
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}
</style>
