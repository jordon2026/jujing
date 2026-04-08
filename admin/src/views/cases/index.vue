<template>
  <div class="cases-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>案例管理</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>添加案例
          </el-button>
        </div>
      </template>
      
      <!-- 筛选 -->
      <div class="filter-bar">
        <el-radio-group v-model="filter" @change="handleFilter">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="website">网站建设</el-radio-button>
          <el-radio-button label="app">APP开发</el-radio-button>
          <el-radio-button label="wechat">微信开发</el-radio-button>
          <el-radio-button label="miniapp">小程序</el-radio-button>
        </el-radio-group>
      </div>
      
      <el-table :data="cases" v-loading="loading" border>
        <el-table-column type="index" width="60" label="序号" />
        <el-table-column prop="title" label="案例名称" min-width="150" />
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            <el-tag :type="getCategoryType(row.category)">
              {{ getCategoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadCases"
          @current-change="loadCases"
        />
      </div>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑案例' : '添加案例'"
      width="600px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="案例名称">
          <el-input v-model="form.title" placeholder="请输入案例名称" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category" placeholder="请选择分类" style="width: 100%;">
            <el-option label="网站建设" value="website" />
            <el-option label="APP开发" value="app" />
            <el-option label="微信开发" value="wechat" />
            <el-option label="小程序" value="miniapp" />
            <el-option label="平台开发" value="platform" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入案例描述"
          />
        </el-form-item>
        <el-form-item label="图标/颜色">
          <el-input v-model="form.icon" placeholder="例如：🏛️" />
        </el-form-item>
        <el-form-item label="背景色">
          <el-color-picker v-model="form.bgColor" show-alpha />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getCases, createCase, updateCase, deleteCase } from '@/api/cases'

const cases = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const filter = ref('all')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const form = ref({
  title: '',
  category: '',
  description: '',
  icon: '🏛️',
  bgColor: 'linear-gradient(135deg,#0a1628,#1a3a5c)'
})

const categoryMap = {
  website: { label: '网站建设', type: 'primary' },
  app: { label: 'APP开发', type: 'success' },
  wechat: { label: '微信开发', type: 'warning' },
  miniapp: { label: '小程序', type: 'info' },
  platform: { label: '平台开发', type: 'danger' }
}

const getCategoryLabel = (category) => categoryMap[category]?.label || category
const getCategoryType = (category) => categoryMap[category]?.type || ''

const loadCases = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      pageSize: pageSize.value,
      category: filter.value === 'all' ? '' : filter.value
    }
    const res = await getCases(params)
    cases.value = res.list || []
    total.value = res.total || 0
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleFilter = () => {
  page.value = 1
  loadCases()
}

const handleAdd = () => {
  isEdit.value = false
  currentId.value = null
  form.value = { title: '', category: '', description: '', icon: '🏛️', bgColor: 'linear-gradient(135deg,#0a1628,#1a3a5c)' }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  currentId.value = row.id
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该案例吗？', '提示', { type: 'warning' })
    await deleteCase(row.id)
    ElMessage.success('删除成功')
    loadCases()
  } catch (error) {
    if (error !== 'cancel') console.error(error)
  }
}

const handleSave = async () => {
  if (!form.value.title || !form.value.category) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  try {
    if (isEdit.value) {
      await updateCase(currentId.value, form.value)
    } else {
      await createCase(form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadCases()
  } catch (error) {
    console.error(error)
  }
}

onMounted(loadCases)
</script>

<style scoped lang="scss">
.cases-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .filter-bar {
    margin-bottom: 20px;
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
