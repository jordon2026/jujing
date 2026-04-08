<template>
  <div class="columns-page">
    <el-card class="page-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <h3>栏目管理</h3>
            <p class="subtitle">管理网站栏目结构，支持增删改查和排序</p>
          </div>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>新增栏目
          </el-button>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="columnsList"
        row-key="id"
        style="width: 100%"
      >
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="name" label="栏目名称" min-width="150">
          <template #default="{ row }">
            <div class="column-name">
              <span class="name">{{ row.name }}</span>
              <el-tag v-if="isProtected(row.code)" size="small" type="warning">系统</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="栏目编码" width="120" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.type === 'list' ? 'success' : 'info'" size="small">
              {{ row.type === 'list' ? '列表' : '单页' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="sort" label="排序" width="80" align="center" />
        <el-table-column label="显示状态" width="100" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.isShow"
              :disabled="isProtected(row.code)"
              @change="handleToggleStatus(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
            <el-button 
              type="danger" 
              link 
              :disabled="isProtected(row.code)"
              @click="handleDelete(row)"
            >
              <el-icon><Delete /></el-icon>删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 拖拽排序提示 -->
      <div class="sort-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>提示：栏目按"排序"字段从小到大排列，可在编辑中修改排序值</span>
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑栏目' : '新增栏目'"
      width="500px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="栏目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入栏目名称" />
        </el-form-item>
        <el-form-item label="栏目编码" prop="code">
          <el-input 
            v-model="form.code" 
            placeholder="请输入栏目编码，如：news"
            :disabled="isEdit && isProtected(form.code)"
          />
          <span class="form-tip">唯一标识，创建后不可修改（系统栏目除外）</span>
        </el-form-item>
        <el-form-item label="栏目类型" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio label="single">单页</el-radio>
            <el-radio label="list">列表</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="排序号" prop="sort">
          <el-input-number v-model="form.sort" :min="0" :max="999" />
          <span class="form-tip">数字越小排序越靠前</span>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入栏目描述"
          />
        </el-form-item>
        <el-form-item label="显示状态" prop="isShow">
          <el-switch v-model="form.isShow" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, InfoFilled } from '@element-plus/icons-vue'
import { getColumns, createColumn, updateColumn, deleteColumn, toggleColumnStatus } from '@/api/columns'

const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const columnsList = ref([])
const formRef = ref()

const form = reactive({
  id: null,
  name: '',
  code: '',
  type: 'single',
  description: '',
  sort: 0,
  isShow: true
})

const rules = {
  name: [
    { required: true, message: '请输入栏目名称', trigger: 'blur' },
    { min: 2, max: 20, message: '长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入栏目编码', trigger: 'blur' },
    { pattern: /^[a-z][a-z0-9_]*$/, message: '以小写字母开头，只能包含小写字母、数字和下划线', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择栏目类型', trigger: 'change' }
  ]
}

// 系统保护栏目
const protectedCodes = ['hero', 'about', 'contact']

const isProtected = (code) => {
  return protectedCodes.includes(code)
}

// 获取栏目列表
const fetchColumns = async () => {
  loading.value = true
  try {
    const data = await getColumns()
    columnsList.value = data || []
  } catch (error) {
    console.error('获取栏目列表失败:', error)
    ElMessage.error('获取栏目列表失败')
  } finally {
    loading.value = false
  }
}

// 新增
const handleAdd = () => {
  isEdit.value = false
  form.id = null
  form.name = ''
  form.code = ''
  form.type = 'single'
  form.description = ''
  form.sort = columnsList.value.length + 1
  form.isShow = true
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row) => {
  isEdit.value = true
  form.id = row.id
  form.name = row.name
  form.code = row.code
  form.type = row.type
  form.description = row.description || ''
  form.sort = row.sort || row.id
  form.isShow = row.isShow !== false
  dialogVisible.value = true
}

// 提交
const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    if (isEdit.value) {
      await updateColumn(form.id, form)
      ElMessage.success('更新成功')
    } else {
      await createColumn(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    // 延迟一下再刷新，确保后端数据已更新
    setTimeout(() => {
      fetchColumns()
    }, 300)
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

// 删除
const handleDelete = (row) => {
  if (isProtected(row.code)) {
    ElMessage.warning('系统内置栏目不能删除')
    return
  }
  
  ElMessageBox.confirm(
    `确定要删除栏目"${row.name}"吗？删除后不可恢复！`,
    '确认删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteColumn(row.id)
      ElMessage.success('删除成功')
      fetchColumns()
    } catch (error) {
      console.error('删除失败:', error)
      ElMessage.error(error.message || '删除失败')
    }
  }).catch(() => {})
}

// 切换状态
const handleToggleStatus = async (row) => {
  try {
    const result = await toggleColumnStatus(row.id)
    // 使用后端返回的最新状态
    if (result && result.isShow !== undefined) {
      row.isShow = result.isShow
    }
    ElMessage.success('状态更新成功')
  } catch (error) {
    // 恢复原状态
    row.isShow = !row.isShow
    console.error('切换状态失败:', error)
  }
}

onMounted(() => {
  fetchColumns()
})
</script>

<style scoped lang="scss">
.columns-page {
  padding: 20px;
  
  .page-card {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-left {
        h3 {
          margin: 0 0 4px;
          font-size: 18px;
        }
        .subtitle {
          margin: 0;
          font-size: 13px;
          color: #909399;
        }
      }
    }
    
    .column-name {
      display: flex;
      align-items: center;
      gap: 8px;
      
      .name {
        font-weight: 500;
      }
    }
    
    .sort-tip {
      margin-top: 16px;
      padding: 12px 16px;
      background: #f5f7fa;
      border-radius: 4px;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: #606266;
      
      .el-icon {
        color: #909399;
      }
    }
  }
  
  .form-tip {
    display: block;
    margin-top: 4px;
    font-size: 12px;
    color: #909399;
  }
}
</style>
