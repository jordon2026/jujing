<template>
  <div class="news-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>新闻动态管理</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>发布新闻
          </el-button>
        </div>
      </template>
      
      <el-table :data="news" v-loading="loading" border>
        <el-table-column type="index" width="60" label="序号" />
        <el-table-column label="日期" width="100">
          <template #default="{ row }">
            <div class="news-date">
              <div class="day">{{ row.day }}</div>
              <div class="month-year">{{ row.month }}<br/>{{ row.year }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="summary" label="摘要" show-overflow-tooltip />
        <el-table-column prop="tag" label="标签" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ row.tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadNews"
          @current-change="loadNews"
        />
      </div>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑新闻' : '发布新闻'"
      width="700px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="请输入新闻标题" />
        </el-form-item>
        <el-form-item label="日期">
          <el-date-picker
            v-model="form.date"
            type="date"
            placeholder="选择日期"
            style="width: 100%;"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="form.tag" placeholder="例如：企业网站建设" />
        </el-form-item>
        <el-form-item label="摘要">
          <el-input
            v-model="form.summary"
            type="textarea"
            :rows="3"
            placeholder="请输入新闻摘要"
          />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            placeholder="请输入新闻详细内容"
          />
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
import { getNews, createNews, updateNews, deleteNews } from '@/api/news'

const news = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const form = ref({
  title: '',
  date: '',
  tag: '',
  summary: '',
  content: ''
})

const parseDate = (dateStr) => {
  const date = new Date(dateStr)
  return {
    day: String(date.getDate()).padStart(2, '0'),
    month: String(date.getMonth() + 1).padStart(2, '0') + '月',
    year: date.getFullYear()
  }
}

const loadNews = async () => {
  loading.value = true
  try {
    const res = await getNews({ page: page.value, pageSize: pageSize.value })
    news.value = (res.list || []).map(item => ({
      ...item,
      ...parseDate(item.date)
    }))
    total.value = res.total || 0
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  currentId.value = null
  form.value = { title: '', date: '', tag: '', summary: '', content: '' }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  currentId.value = row.id
  form.value = { 
    title: row.title,
    date: row.date,
    tag: row.tag,
    summary: row.summary,
    content: row.content
  }
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该新闻吗？', '提示', { type: 'warning' })
    await deleteNews(row.id)
    ElMessage.success('删除成功')
    loadNews()
  } catch (error) {
    if (error !== 'cancel') console.error(error)
  }
}

const handleSave = async () => {
  if (!form.value.title || !form.value.date) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  try {
    if (isEdit.value) {
      await updateNews(currentId.value, form.value)
    } else {
      await createNews(form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadNews()
  } catch (error) {
    console.error(error)
  }
}

onMounted(loadNews)
</script>

<style scoped lang="scss">
.news-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .news-date {
    display: flex;
    align-items: baseline;
    gap: 6px;
    
    .day {
      font-size: 1.5rem;
      font-weight: 700;
      color: #1890ff;
    }
    
    .month-year {
      font-size: 0.75rem;
      color: #8c8c8c;
      line-height: 1.2;
    }
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
