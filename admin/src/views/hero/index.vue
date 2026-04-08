<template>
  <div class="hero-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>首页 Hero 区域管理</span>
          <el-button type="primary" @click="saveHero">保存修改</el-button>
        </div>
      </template>
      
      <el-form :model="heroForm" label-width="100px">
        <el-form-item label="主标题">
          <el-input v-model="heroForm.title" placeholder="请输入主标题" />
        </el-form-item>
        
        <el-form-item label="副标题">
          <el-input v-model="heroForm.subtitle" placeholder="请输入副标题" />
        </el-form-item>
        
        <el-form-item label="描述文字">
          <el-input
            v-model="heroForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述文字"
          />
        </el-form-item>
        
        <el-form-item label="徽章文字">
          <el-input v-model="heroForm.badge" placeholder="例如：高新技术企业 · 华为云合作伙伴" />
        </el-form-item>
        
        <el-form-item label="主按钮文字">
          <el-input v-model="heroForm.primaryBtn" placeholder="例如：了解我们的服务" />
        </el-form-item>
        
        <el-form-item label="次按钮文字">
          <el-input v-model="heroForm.secondaryBtn" placeholder="例如：查看成功案例" />
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>统计数据管理</span>
          <el-button type="primary" @click="saveStats">保存修改</el-button>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :lg="6" v-for="(stat, index) in stats" :key="index">
          <el-card class="stat-edit-card" shadow="never">
            <el-form label-width="60px">
              <el-form-item label="数值">
                <el-input v-model="stat.value" placeholder="例如：100+" />
              </el-form-item>
              <el-form-item label="标签">
                <el-input v-model="stat.label" placeholder="例如：技术团队" />
              </el-form-item>
            </el-form>
          </el-card>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getHero, updateHero, getStats, updateStats } from '@/api/hero'

const heroForm = ref({
  title: '专注网站建设',
  subtitle: '平台系统开发10年',
  description: '北京聚景科技有限公司，致力于互联网品牌建设与网络营销，专业领域包括网站建设、APP开发、微信开发、小程序定制开发、H5互动设计、VR应用开发、AI智能体开发、智能体本地化部署服务等，为客户提供综合性数字化创新服务。',
  badge: '高新技术企业 · 华为云合作伙伴',
  primaryBtn: '了解我们的服务',
  secondaryBtn: '查看成功案例'
})

const stats = ref([
  { value: '100+', label: '技术团队' },
  { value: '10+', label: '年行业经验' },
  { value: '500+', label: '服务客户' },
  { value: '800+', label: '成功案例' }
])

const saveHero = async () => {
  try {
    await updateHero(heroForm.value)
    ElMessage.success('保存成功')
  } catch (error) {
    console.error(error)
  }
}

const saveStats = async () => {
  try {
    await updateStats(stats.value)
    ElMessage.success('保存成功')
  } catch (error) {
    console.error(error)
  }
}

onMounted(async () => {
  try {
    const heroRes = await getHero()
    if (heroRes) heroForm.value = heroRes
    
    const statsRes = await getStats()
    if (statsRes) stats.value = statsRes
  } catch (error) {
    console.error(error)
  }
})
</script>

<style scoped lang="scss">
.hero-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .stat-edit-card {
    margin-bottom: 16px;
    
    :deep(.el-card__body) {
      padding: 16px;
    }
  }
}
</style>
