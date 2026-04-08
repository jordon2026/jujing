<template>
  <div class="contacts-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>客户咨询</span>
          <div class="header-actions">
            <el-radio-group v-model="statusFilter" @change="loadContacts">
              <el-radio-button label="">全部</el-radio-button>
              <el-radio-button label="pending">待处理</el-radio-button>
              <el-radio-button label="processed">已处理</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>
      
      <el-table :data="contacts" v-loading="loading" border>
        <el-table-column type="index" width="60" label="序号" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="电话" width="120" />
        <el-table-column prop="company" label="公司名称" width="150" show-overflow-tooltip />
        <el-table-column prop="service" label="需求类型" width="120" />
        <el-table-column prop="description" label="需求描述" show-overflow-tooltip />
        <el-table-column prop="created_at" label="提交时间" width="150">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'pending' ? 'warning' : 'success'">
              {{ row.status === 'pending' ? '待处理' : '已处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'pending'" 
              link 
              type="primary" 
              @click="handleProcess(row)"
            >
              标记处理
            </el-button>
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
          @size-change="loadContacts"
          @current-change="loadContacts"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getContacts, updateContactStatus, deleteContact } from '@/api/contacts'

const contacts = ref([])
const loading = ref(false)
const statusFilter = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  const date = new Date(datetime)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadContacts = async () => {
  loading.value = true
  try {
    const params = {
      page: page.value,
      pageSize: pageSize.value,
      status: statusFilter.value
    }
    const res = await getContacts(params)
    contacts.value = res.list || []
    total.value = res.total || 0
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleProcess = async (row) => {
  try {
    await updateContactStatus(row.id, 'processed')
    ElMessage.success('已标记为处理')
    loadContacts()
  } catch (error) {
    console.error(error)
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该咨询记录吗？', '提示', { type: 'warning' })
    await deleteContact(row.id)
    ElMessage.success('删除成功')
    loadContacts()
  } catch (error) {
    if (error !== 'cancel') console.error(error)
  }
}

onMounted(loadContacts)
</script>

<style scoped lang="scss">
.contacts-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
