<template>
  <router-view />
</template>

<script setup>
import { useUserStore } from './stores/user'

const userStore = useUserStore()

// 如果已登录，在后台刷新用户权限（不会阻止导航）
if (userStore.isLoggedIn()) {
  userStore.refreshUserInfo()
}
</script>

<style>
/* 全局样式重置和基础样式 */
:root {
  --primary-color: rgb(0, 120, 212);
  --primary-hover-color: rgb(0, 102, 181);
  --primary-active-color: rgb(0, 153, 255);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
  font-size: 14px;
  color: #303133;
  background-color: #f0f2f5;
}

#app {
  height: 100%;
}

/* Element Plus 全局样式覆盖 */
.el-card {
  border-radius: 8px;
}

.el-card__header {
  background-color: #fafafa;
  border-bottom: 1px solid #ebeef5;
}

.el-button--primary {
  --el-button-bg-color: rgb(0, 120, 212);
  --el-button-border-color: rgb(0, 120, 212);
  --el-button-hover-bg-color: rgb(0, 102, 181);
  --el-button-hover-border-color: rgb(0, 102, 181);
}

.el-button--primary:hover {
  background-color: rgb(0, 102, 181) !important;
  border-color: rgb(0, 102, 181) !important;
}

.el-button--primary.is-active,
.el-button--primary:active {
  background-color: rgb(0, 153, 255) !important;
  border-color: rgb(0, 153, 255) !important;
}

.el-table th {
  background-color: #fafafa;
  color: #606266;
  font-weight: 600;
}

/* Element Plus 主题色覆盖 */
.el-color-primary {
  color: rgb(0, 120, 212) !important;
}

.el-link.el-link--primary {
  color: rgb(0, 120, 212) !important;
}

.el-menu-item.is-active {
  background-color: rgb(0, 120, 212) !important;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: rgb(0, 120, 212);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgb(0, 102, 181);
}
</style>
