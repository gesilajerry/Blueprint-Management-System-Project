<template>
  <div class="core-parts-page">
    <div class="page-header">
      <h2>核心部件词库管理</h2>
      <div>
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
          新增关键词
        </el-button>
      </div>
    </div>

    <el-alert
      title="词库说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 15px"
    >
      <template #title>
        <div style="font-size: 13px">
          用于系统辅助建议图纸保密等级。当图纸名称命中词库关键词时，系统会提示"疑似核心部件"，建议定为 A 类。
          <br>
          <span style="color: #909399; font-size: 12px">仅研发管理员可管理词库</span>
        </div>
      </template>
    </el-alert>

    <el-card class="table-card">
      <!-- 搜索区 -->
      <el-form :inline="true" class="search-form" style="margin-bottom: 15px">
        <el-form-item label="关键词">
          <el-input
            v-model="searchKeyword"
            placeholder="请输入关键词"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 表格 -->
      <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
        <el-table-column prop="keyword" label="关键词" min-width="200" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.created_at ? row.created_at.replace('T', ' ').substring(0, 16) : '' }}
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" label="创建人" width="100" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新增对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="新增关键词"
      width="500px"
    >
      <el-form :model="formData" label-width="100px">
        <el-form-item label="关键词" required>
          <el-input
            v-model="formData.keyword"
            placeholder="如：电机、控制系统、传动机构"
            maxlength="50"
            show-word-limit
          />
          <div class="form-tip">
            支持中文词汇、词组，系统将进行模糊匹配
          </div>
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
    <el-dialog v-model="showImportDialog" title="批量导入关键词" width="450px">
      <el-alert type="info" :closable="false" style="margin-bottom: 15px">
        <template #title>
          请上传 CSV 文件，文件应包含 <b>keyword</b> 列。支持合并导入，已存在的关键词会自动跳过。
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
import { api, postForm } from '../utils/api'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()
const loading = ref(false)
const submitting = ref(false)
const searchKeyword = ref('')
const dialogVisible = ref(false)
const showImportDialog = ref(false)
const importing = ref(false)
const uploadRef = ref(null)
const selectedFile = ref(null)

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const tableData = ref([])

const formData = reactive({
  keyword: ''
})

// 加载词库列表
const loadCoreParts = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    if (searchKeyword.value) params.keyword = searchKeyword.value

    const res = await api.coreParts.list(params)
    tableData.value = res.data?.items || []
    pagination.total = res.data?.total || 0

    // 简化处理：创建人统一显示为"管理员"
    tableData.value.forEach(item => {
      item.creator_name = '管理员'
    })
  } catch (error) {
    console.error('加载词库列表失败:', error)
    ElMessage.error('加载词库列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadCoreParts()
})

const handleSearch = () => {
  pagination.page = 1
  loadCoreParts()
}

const handleReset = () => {
  searchKeyword.value = ''
  pagination.page = 1
  loadCoreParts()
}

const handleAdd = () => {
  formData.keyword = ''
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除关键词"${row.keyword}"吗？`, '提示', {
      type: 'warning'
    })

    await api.coreParts.delete(row.id)
    ElMessage.success('已删除')
    loadCoreParts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败：' + error.message)
    }
  }
}

const handleSubmit = async () => {
  if (!formData.keyword.trim()) {
    ElMessage.warning('请输入关键词')
    return
  }

  submitting.value = true
  try {
    await postForm('/core-parts', { keyword: formData.keyword })
    ElMessage.success('新增成功')
    dialogVisible.value = false
    loadCoreParts()
  } catch (error) {
    console.error('新增失败:', error)
    ElMessage.error('新增失败：' + error.message)
  } finally {
    submitting.value = false
  }
}

const handleExport = async () => {
  try {
    const blob = await api.coreParts.export()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'core_parts_keywords.csv'
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
    const result = await api.coreParts.import(selectedFile.value)
    ElMessage.success(`导入完成：成功 ${result.data?.success_count || 0} 条，跳过 ${result.data?.skipped_count || 0} 条`)
    showImportDialog.value = false
    selectedFile.value = null
    loadCoreParts()
  } catch (error) {
    ElMessage.error('导入失败：' + error.message)
  } finally {
    importing.value = false
  }
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  loadCoreParts()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadCoreParts()
}
</script>

<style scoped>
.core-parts-page {
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

.table-card {
  min-height: 400px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
