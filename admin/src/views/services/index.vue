<template>
  <div class="services-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>服务项目管理</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>添加服务
          </el-button>
        </div>
      </template>
      
      <el-table :data="services" v-loading="loading" border>
        <el-table-column type="index" width="60" label="序号" />
        <el-table-column prop="icon" width="80" label="图标">
          <template #default="{ row }">
            <span style="font-size: 24px;">{{ row.icon }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="服务名称" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column label="标签" width="200">
          <template #default="{ row }">
            <el-tag v-for="tag in row.tags" :key="tag" size="small" style="margin-right: 4px;">
              {{ tag }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑服务' : '添加服务'"
      width="600px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="图标">
          <el-input v-model="form.icon" placeholder="例如：🌐" />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="form.title" placeholder="请输入服务名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入服务描述"
          />
        </el-form-item>
        <el-form-item label="标签">
          <div class="tags-input">
            <el-tag
              v-for="(tag, index) in form.tags"
              :key="index"
              closable
              @close="removeTag(index)"
              style="margin-right: 8px; margin-bottom: 8px;"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-if="inputVisible"
              ref="tagInputRef"
              v-model="inputValue"
              size="small"
              style="width: 100px;"
              @keyup.enter="addTag"
              @blur="addTag"
            />
            <el-button v-else size="small" @click="showInput">+ 添加标签</el-button>
          </div>
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
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getServices, createService, updateService, deleteService } from '@/api/services'

const services = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const tagInputRef = ref()
const inputVisible = ref(false)
const inputValue = ref('')

const form = ref({
  icon: '',
  title: '',
  description: '',
  tags: []
})

const loadServices = async () => {
  loading.value = true
  try {
    const res = await getServices()
    services.value = res || []
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  isEdit.value = false
  currentId.value = null
  form.value = { icon: '', title: '', description: '', tags: [] }
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
    await ElMessageBox.confirm('确定要删除该服务吗？', '提示', { type: 'warning' })
    await deleteService(row.id)
    ElMessage.success('删除成功')
    loadServices()
  } catch (error) {
    if (error !== 'cancel') console.error(error)
  }
}

const handleSave = async () => {
  if (!form.value.title || !form.value.description) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  try {
    if (isEdit.value) {
      await updateService(currentId.value, form.value)
    } else {
      await createService(form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadServices()
  } catch (error) {
    console.error(error)
  }
}

const showInput = () => {
  inputVisible.value = true
  nextTick(() => tagInputRef.value?.focus())
}

const addTag = () => {
  if (inputValue.value && !form.value.tags.includes(inputValue.value)) {
    form.value.tags.push(inputValue.value)
  }
  inputVisible.value = false
  inputValue.value = ''
}

const removeTag = (index) => {
  form.value.tags.splice(index, 1)
}

onMounted(loadServices)
</script>

<style scoped lang="scss">
.services-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .tags-input {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
  }
}
</style>
