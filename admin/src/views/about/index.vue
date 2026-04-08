<template>
  <div class="about-page">
    <!-- 公司信息 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>公司信息</span>
          <el-button type="primary" @click="saveAbout">保存修改</el-button>
        </div>
      </template>
      
      <el-form :model="aboutForm" label-width="100px">
        <el-form-item label="公司名称">
          <el-input v-model="aboutForm.companyName" />
        </el-form-item>
        <el-form-item label="公司简介">
          <el-input
            v-model="aboutForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入公司简介"
          />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="aboutForm.address" />
        </el-form-item>
        <el-form-item label="电话">
          <el-input v-model="aboutForm.phone" />
        </el-form-item>
        <el-form-item label="手机">
          <el-input v-model="aboutForm.mobile" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="aboutForm.email" />
        </el-form-item>
        <el-form-item label="邮编">
          <el-input v-model="aboutForm.zipCode" />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 发展历程 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>发展历程</span>
          <el-button type="primary" @click="handleAddTimeline">
            <el-icon><Plus /></el-icon>添加历程
          </el-button>
        </div>
      </template>
      
      <el-timeline>
        <el-timeline-item
          v-for="(item, index) in timeline"
          :key="item.id"
          :type="index === 0 ? 'primary' : ''"
          :timestamp="item.year"
        >
          <el-card class="timeline-card">
            <template #header>
              <div class="timeline-header">
                <h4>{{ item.title }}</h4>
                <div class="timeline-actions">
                  <el-button link type="primary" @click="handleEditTimeline(item)">编辑</el-button>
                  <el-button link type="danger" @click="handleDeleteTimeline(item)">删除</el-button>
                </div>
              </div>
            </template>
            <p>{{ item.description }}</p>
          </el-card>
        </el-timeline-item>
      </el-timeline>
    </el-card>

    <!-- 编辑历程对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑历程' : '添加历程'"
      width="500px"
    >
      <el-form :model="timelineForm" label-width="80px">
        <el-form-item label="年份">
          <el-input v-model="timelineForm.year" placeholder="例如：2021年" />
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="timelineForm.title" placeholder="请输入标题" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="timelineForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTimeline">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getAbout, updateAbout, getTimeline, createTimeline, updateTimeline, deleteTimeline } from '@/api/about'

const aboutForm = ref({
  companyName: '北京聚景科技有限公司',
  description: '聚景科技自公司创立至今，始终坚持从事网站定制，信息系统开发。公司总部位于北京，秉承实现全网价值营销的理念，以数据为核心，结合营销、内容、技术、研发多维度为客户提供综合性数字化创新服务，帮助传统企业实现"互联网+"转型升级。',
  address: '北京市昌平区龙德紫金2号楼',
  phone: '010-84818211',
  mobile: '131-4686-6478',
  email: 'admin@jujingyun.com',
  zipCode: '102218'
})

const timeline = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)

const timelineForm = ref({
  year: '',
  title: '',
  description: ''
})

const loadAbout = async () => {
  try {
    const res = await getAbout()
    if (res) aboutForm.value = res
  } catch (error) {
    console.error(error)
  }
}

const loadTimeline = async () => {
  try {
    const res = await getTimeline()
    timeline.value = res || []
  } catch (error) {
    console.error(error)
  }
}

const saveAbout = async () => {
  try {
    await updateAbout(aboutForm.value)
    ElMessage.success('保存成功')
  } catch (error) {
    console.error(error)
  }
}

const handleAddTimeline = () => {
  isEdit.value = false
  currentId.value = null
  timelineForm.value = { year: '', title: '', description: '' }
  dialogVisible.value = true
}

const handleEditTimeline = (item) => {
  isEdit.value = true
  currentId.value = item.id
  timelineForm.value = { ...item }
  dialogVisible.value = true
}

const handleDeleteTimeline = async (item) => {
  try {
    await ElMessageBox.confirm('确定要删除该历程吗？', '提示', { type: 'warning' })
    await deleteTimeline(item.id)
    ElMessage.success('删除成功')
    loadTimeline()
  } catch (error) {
    if (error !== 'cancel') console.error(error)
  }
}

const saveTimeline = async () => {
  if (!timelineForm.value.year || !timelineForm.value.title) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  try {
    if (isEdit.value) {
      await updateTimeline(currentId.value, timelineForm.value)
    } else {
      await createTimeline(timelineForm.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    loadTimeline()
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  loadAbout()
  loadTimeline()
})
</script>

<style scoped lang="scss">
.about-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .timeline-card {
    :deep(.el-card__header) {
      padding: 12px 16px;
    }
    
    :deep(.el-card__body) {
      padding: 16px;
    }
  }
  
  .timeline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    h4 {
      margin: 0;
      font-size: 1rem;
    }
  }
  
  .timeline-actions {
    display: flex;
    gap: 8px;
  }
}
</style>
