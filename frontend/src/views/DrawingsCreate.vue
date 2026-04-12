<template>
  <div class="drawing-create-page">
    <el-page-header @back="$router.back()">
      <template #content>
        <span class="page-title">新建图纸</span>
      </template>
    </el-page-header>

    <el-card class="form-card">
      <el-form
        :model="form"
        :rules="rules"
        ref="formRef"
        label-width="140px"
        class="drawing-form"
      >
        <el-divider content-position="left">基础信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="图号">
              <div style="color: #909399; font-size: 13px">提交后系统自动生成</div>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="版本号">
              <span style="color: #67c23a">V1.0</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">图纸信息</el-divider>

        <el-form-item label="所属产品/项目" prop="product_id">
          <el-select
            v-model="form.product_id"
            placeholder="请选择产品/项目"
            style="width: 100%"
            :loading="productsLoading"
            @change="handleProductChange"
          >
            <el-option
              v-for="p in products"
              :key="p.id"
              :label="p.name"
              :value="p.id"
            />
          </el-select>
          <div class="form-tip">图号将根据项目立项编号自动生成</div>
        </el-form-item>

        <el-form-item label="图纸名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入图纸名称" />
        </el-form-item>

        <el-form-item label="所属项目">
          <el-input :model-value="selectedProjectGroupName" placeholder="选择产品后自动显示" readonly />
        </el-form-item>

        <el-divider content-position="left">保密等级认定</el-divider>

        <el-form-item label="是否涉及核心部件" prop="is_core_part">
          <el-checkbox v-model="form.is_core_part" label="涉及核心部件" border />
        </el-form-item>

        <el-form-item label="核心部件关键词" v-if="form.is_core_part">
          <el-checkbox-group v-model="form.core_part_keywords">
            <el-checkbox
              v-for="keyword in corePartKeywords"
              :key="keyword.id"
              :label="keyword.keyword"
              border
            />
          </el-checkbox-group>
          <div class="form-tip">请选择与当前图纸相关的核心部件关键词</div>
        </el-form-item>

        <el-form-item label="保密等级" prop="confidentiality_level">
          <el-select
            v-model="form.confidentiality_level"
            placeholder="请选择保密等级"
            style="width: 100%"
          >
            <el-option label="A 类 - 核心机密" value="A" />
            <el-option label="B 类 - 重要" value="B" />
            <el-option label="C 类 - 一般" value="C" />
          </el-select>
        </el-form-item>

        <el-divider content-position="left">版本文件上传</el-divider>

        <el-alert
          title="首次创建需上传初始版本文件"
          type="info"
          :closable="false"
          show-icon
          style="margin-bottom: 15px"
        >
          <template #title>
            <div style="font-size: 13px">
              支持 DWG、DXF、PDF 等格式，文件大小不超过 500MB
            </div>
          </template>
        </el-alert>

        <el-form-item label="上传文件">
          <el-upload
            ref="uploadRef"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :file-list="fileList"
            :limit="1"
            accept=".dwg,.dxf,.pdf,.step,.stp,.igs,.iges"
          >
            <el-icon class="el-icon--upload">
              <UploadFilled />
            </el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 DWG、DXF、PDF、STEP 等格式，单个文件不超过 500MB
              </div>
            </template>
          </el-upload>
          <div class="form-tip" v-if="selectedFile">
            已选择：{{ selectedFile.name }} ({{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB)
          </div>
        </el-form-item>

        <el-divider content-position="left">知识沉淀信息</el-divider>

        <el-form-item label="用途背景" prop="purpose">
          <el-input
            v-model="form.purpose"
            type="textarea"
            :rows="3"
            placeholder="请描述该图纸的用途背景"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="关键材料">
          <el-input
            v-model="form.material"
            placeholder="如：铝合金 6061、不锈钢 304"
            maxlength="200"
          />
        </el-form-item>

        <el-form-item label="关键尺寸">
          <el-input
            v-model="form.dimensions"
            placeholder="如：500×300×200mm"
            maxlength="200"
          />
        </el-form-item>

        <el-form-item label="保密要点">
          <el-input
            v-model="form.secret_points"
            type="textarea"
            :rows="3"
            placeholder="请描述该图纸的保密要点和核心技术"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <el-divider />

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            提交
          </el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onBeforeMount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled, Upload } from '@element-plus/icons-vue'
import { api, uploadFile } from '../utils/api'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const uploadRef = ref(null)
const submitting = ref(false)
const productsLoading = ref(false)

const products = ref([])
const projectGroups = ref([])
const corePartKeywords = ref([])
const fileList = ref([])
const selectedFile = ref(null)
const selectedProjectGroupName = ref('')

const form = reactive({
  product_id: '',
  name: '',
  is_core_part: false,
  core_part_keywords: [],
  confidentiality_level: '',
  purpose: '',
  material: '',
  dimensions: '',
  secret_points: ''
})

const rules = {
  product_id: [{ required: true, message: '请选择产品/项目', trigger: 'change' }],
  name: [{ required: true, message: '请输入图纸名称', trigger: 'blur' }],
  confidentiality_level: [{ required: true, message: '请选择保密等级', trigger: 'change' }],
  file: [{ required: true, message: '请上传图纸文件', trigger: 'change' }]
}

// 加载产品列表（根据用户权限过滤，只获取进行中的产品）
const loadProducts = async () => {
  productsLoading.value = true
  try {
    // 获取所有进行中的产品
    const res = await api.products.list({ page: 1, size: 100, status: 'active' })
    let filteredProducts = res.data?.items || []

    // 如果用户有 viewAllDrawings 权限（CTO/管理员/审定人），显示所有产品
    // 否则只显示用户所在项目组的产品
    if (!userStore.hasPermission('viewAllDrawings')) {
      const groupsRes = await api.users.getMyProjectGroups()
      const userGroupIds = (groupsRes.data || []).map(g => g.id)
      if (userGroupIds.length > 0) {
        filteredProducts = filteredProducts.filter(p => p.project_group_id && userGroupIds.includes(p.project_group_id))
      }
    }

    products.value = filteredProducts

    // 同时加载项目组信息用于显示名称（只加载进行中的）
    const groupsAllRes = await api.projectGroups.list({ page: 1, size: 100, status: 'active' })
    projectGroups.value = groupsAllRes.data?.items || []
  } catch (error) {
    console.error('加载产品列表失败:', error)
    // 出错时尝试加载所有产品
    try {
      const res = await api.products.list({ page: 1, size: 100 })
      products.value = res.data?.items || []
    } catch (e) {
      console.error('加载产品列表也失败:', e)
    }
  } finally {
    productsLoading.value = false
  }
}

// 加载核心部件词库
const loadCorePartKeywords = async () => {
  try {
    const res = await api.coreParts.list({ page: 1, size: 100 })
    corePartKeywords.value = res.data?.items || []
  } catch (error) {
    console.error('加载核心部件词库失败:', error)
  }
}

// 产品选择变化时，自动设置项目组
const handleProductChange = (productId) => {
  const product = products.value.find(p => p.id === productId)
  if (product && product.project_group_id) {
    const group = projectGroups.value.find(g => g.id === product.project_group_id)
    selectedProjectGroupName.value = group?.name || product.project_group_id
  } else {
    selectedProjectGroupName.value = ''
  }
}

onBeforeMount(() => {
  loadProducts()
  loadCorePartKeywords()
})

const handleFileChange = (file) => {
  console.log('File changed:', file?.raw)
  selectedFile.value = file?.raw
  // 验证文件大小
  if (file?.raw && file.raw.size > 500 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 500MB')
    selectedFile.value = null
    fileList.value = []
    return
  }
  // 验证文件类型
  const allowedTypes = ['.dwg', '.dxf', '.pdf', '.step', '.stp', '.igs', '.iges']
  const ext = file?.name.toLowerCase().substring(file.name.lastIndexOf('.'))
  if (file && !allowedTypes.includes(ext)) {
    ElMessage.error('不支持的文件类型，请上传 DWG、DXF、PDF 或 STEP 格式')
    selectedFile.value = null
    fileList.value = []
    return
  }
  console.log('Selected file validated:', selectedFile.value)
}

const handleFileRemove = () => {
  selectedFile.value = null
}

const handleSubmit = async () => {
  if (!formRef.value) return

  // 验证文件是否已选择
  if (!selectedFile.value) {
    ElMessage.error('请上传图纸文件')
    return
  }

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        // 第一步：创建图纸记录（包含知识沉淀字段）
        const createRes = await api.drawings.create({
          product_id: form.product_id,
          name: form.name,
          is_core_part: form.is_core_part,
          confidentiality_level: form.confidentiality_level,
          purpose: form.purpose,
          material: form.material,
          dimensions: form.dimensions,
          secret_points: form.secret_points,
          // 核心部件关键词以逗号分隔的 ID 字符串
          core_part_keywords: form.core_part_keywords?.join(',') || ''
        })

        const drawingId = createRes.data?.id
        if (!drawingId) {
          throw new Error('创建图纸失败，未返回图纸 ID')
        }

        // 第二步：上传初始版本文件
        await uploadFile(`/drawings/${drawingId}/versions`, selectedFile.value, {})

        ElMessage.success(`图纸创建成功！图号：${createRes.data.drawing_no}`)
        setTimeout(() => {
          router.push('/drawings')
        }, 1000)
      } catch (error) {
        console.error('创建图纸失败:', error)
        ElMessage.error('创建失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
  })
}
</script>

<style scoped>
.drawing-create-page {
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

.drawing-form {
  padding: 0 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

:deep(.el-upload) {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
  padding: 40px 20px;
}

:deep(.el-upload__text) {
  color: #606266;
  font-size: 14px;
}

:deep(.el-upload__text em) {
  color: #409eff;
  font-style: normal;
}

:deep(.el-upload__tip) {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}
</style>
