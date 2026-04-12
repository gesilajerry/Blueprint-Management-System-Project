<template>
  <div class="upload-version-page">
    <el-page-header @back="$router.back()">
      <template #content>
        <span class="page-title">上传新版本</span>
      </template>
    </el-page-header>

    <el-card class="form-card">
      <!-- 当前版本信息 -->
      <el-alert
        title="当前图纸信息"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 20px"
      >
        <template #title>
          <div style="font-size: 13px">
            <strong>图号：</strong>{{ drawingInfo.drawingNo}}
            <strong style="margin-left: 20px">名称：</strong>{{ drawingInfo.name }}
            <strong style="margin-left: 20px">当前版本：</strong>
            <el-tag size="small">{{ drawingInfo.version }}</el-tag>
          </div>
        </template>
      </el-alert>

      <el-form
        :model="form"
        :rules="rules"
        ref="formRef"
        label-width="140px"
        class="upload-form"
      >
        <el-form-item label="新版本号" prop="newVersion">
          <el-input v-model="form.newVersion" :value="nextVersion" readonly />
          <div class="form-tip">
            系统自动生成：小版本号 +1（如 V1.0 → V1.1）
          </div>
        </el-form-item>

        <el-divider content-position="left">变更说明</el-divider>

        <el-form-item label="变更类型" prop="changeType">
          <el-checkbox-group v-model="form.changeType">
            <el-checkbox value="optimize">优化设计</el-checkbox>
            <el-checkbox value="fix">修复问题</el-checkbox>
            <el-checkbox value="supplier">适配供应商</el-checkbox>
            <el-checkbox value="cost">成本降低</el-checkbox>
            <el-checkbox value="other">其他</el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="变更原因" prop="changeReason">
          <el-input
            v-model="form.changeReason"
            type="textarea"
            :rows="4"
            placeholder="请说明本次变更的原因和主要内容"
          />
        </el-form-item>

        <el-form-item label="关联问题单号" prop="issueNo">
          <el-input v-model="form.issueNo" placeholder="如：BUG-2026-001（可选）" />
        </el-form-item>

        <el-divider content-position="left">文件上传</el-divider>

        <el-form-item label="上传新文件" prop="file">
          <el-upload
            ref="uploadRef"
            drag
            :auto-upload="false"
            :limit="1"
            :on-change="handleFileChange"
            class="upload-area"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 DWG、PDF、SolidWorks、CAD 等格式，单文件≤500MB
              </div>
            </template>
          </el-upload>
          <div class="form-tip">
            文件将存储在：/data/drawings/{图号}/{{ nextVersion }}/
          </div>
        </el-form-item>

        <el-divider />

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            上传新版本
          </el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { api } from '../utils/api'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const uploading = ref(false)
const submitting = ref(false)

const drawingInfo = reactive({
  drawingNo: '',
  name: '',
  version: 'V1.0'
})

const form = reactive({
  newVersion: '',
  changeType: [],
  changeReason: '',
  issueNo: '',
  file: null
})

const rules = {
  changeReason: [{ required: true, message: '请填写变更原因', trigger: 'blur' }]
}

const nextVersion = computed(() => {
  const parts = drawingInfo.version.replace('V', '').split('.')
  parts[1] = parseInt(parts[1]) + 1
  return `V${parts.join('.')}`
})

// 加载图纸信息
const loadDrawingInfo = async () => {
  try {
    const res = await api.drawings.get(route.params.id)
    const data = res.data
    drawingInfo.drawingNo = data.drawing_no
    drawingInfo.name = data.name

    // 获取当前版本号
    const versionsRes = await api.drawings.getVersions(route.params.id)
    const versions = versionsRes.data || []
    const latestVersion = versions.find(v => v.is_latest)
    if (latestVersion) {
      drawingInfo.version = latestVersion.version_no
    }
  } catch (error) {
    console.error('加载图纸信息失败:', error)
    ElMessage.error('加载图纸信息失败')
  }
}

onMounted(() => {
  loadDrawingInfo()
})

const handleFileChange = (file) => {
  form.file = file.raw
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      if (!form.file) {
        ElMessage.warning('请上传文件')
        return
      }

      submitting.value = true
      try {
        const formData = {
          change_types: form.changeType.join(','),
          change_reason: form.changeReason,
          related_issue: form.issueNo
        }

        await api.drawings.uploadVersion(route.params.id, form.file, formData)
        ElMessage.success(`版本已更新至 ${nextVersion.value}`)
        setTimeout(() => {
          router.push(`/drawings/${route.params.id}`)
        }, 1000)
      } catch (error) {
        console.error('上传失败:', error)
        ElMessage.error('上传失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
  })
}
</script>

<style scoped>
.upload-version-page {
  padding: 0;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
}

.form-card {
  margin-top: 15px;
  max-width: 800px;
}

.upload-form {
  padding: 0 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.upload-area {
  width: 100%;
}
</style>
