<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo-container">
          <div class="company-logo">
            <img src="/logo.png" alt="Logo" class="logo-img" />
            <span class="logo-text">图纸管理系统</span>
          </div>
        </div>
        <h1>Blueprint Management System</h1>
        <p class="subtitle">企业内部图纸全生命周期管理平台</p>
      </div>

      <el-form :model="loginForm" :rules="rules" ref="loginFormRef" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p>© 2026 图纸管理系统 - 内部系统 授权访问</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const apiUrl = '/api/auth/login'
        console.log('正在请求:', apiUrl)

        const response = await fetch(apiUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: loginForm.username, password: loginForm.password })
        })

        console.log('响应状态:', response.status)

        const data = await response.json()
        console.log('响应数据:', data)

        if (response.ok) {
          // 保存 token
          localStorage.setItem('token', data.data.access_token)

          // 用 userStore 保存用户信息和权限
          userStore.setUserInfo(data.data.user, data.data.access_token)

          // 刷新获取完整权限
          await userStore.refreshUserInfo()

          ElMessage.success('登录成功')
          router.push('/dashboard')
        } else {
          ElMessage.error(data.detail || data.message || '登录失败')
        }
      } catch (error) {
        console.error('登录错误详情:', error)
        ElMessage.error(`网络错误：${error.message || '请检查后端服务是否运行'}`)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 420px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.company-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #409EFF 0%, #0066cc 100%);
  border-radius: 8px;
  color: #fff;
}

.logo-img {
  height: 32px;
  width: auto;
}

.logo-text {
  font-size: 20px;
  font-weight: bold;
}

.login-header h1 {
  color: #303133;
  font-size: 24px;
  margin-bottom: 8px;
}

.subtitle {
  color: #909399;
  font-size: 13px;
}

.login-form {
  margin-top: 20px;
}

.login-footer {
  margin-top: 30px;
  text-align: center;
  color: #909399;
  font-size: 12px;
}
</style>
