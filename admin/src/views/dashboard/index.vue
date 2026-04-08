<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #e6f7ff; color: #1890ff;">
            <el-icon><View /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">12,580</div>
            <div class="stat-label">今日访问量</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #f6ffed; color: #52c41a;">
            <el-icon><Briefcase /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.cases }}</div>
            <div class="stat-label">案例总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #fff7e6; color: #fa8c16;">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.news }}</div>
            <div class="stat-label">新闻动态</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-icon" style="background: #fff1f0; color: #f5222d;">
            <el-icon><Message /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.contacts }}</div>
            <div class="stat-label">待处理咨询</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-row :gutter="20" class="quick-actions">
      <el-col :span="24">
        <el-card title="快捷操作">
          <template #header>
            <div class="card-header">
              <span>快捷操作</span>
            </div>
          </template>
          <div class="action-list">
            <div class="action-item" @click="$router.push('/cases')">
              <div class="action-icon" style="background: #e6f7ff; color: #1890ff;">
                <el-icon><Plus /></el-icon>
              </div>
              <span>添加案例</span>
            </div>
            <div class="action-item" @click="$router.push('/news')">
              <div class="action-icon" style="background: #f6ffed; color: #52c41a;">
                <el-icon><EditPen /></el-icon>
              </div>
              <span>发布新闻</span>
            </div>
            <div class="action-item" @click="$router.push('/services')">
              <div class="action-icon" style="background: #fff7e6; color: #fa8c16;">
                <el-icon><Service /></el-icon>
              </div>
              <span>管理服务</span>
            </div>
            <div class="action-item" @click="$router.push('/contacts')">
              <div class="action-icon" style="background: #fff1f0; color: #f5222d;">
                <el-icon><Message /></el-icon>
              </div>
              <span>查看留言</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近动态 -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最新咨询</span>
              <el-button text @click="$router.push('/contacts')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentContacts" style="width: 100%">
            <el-table-column prop="name" label="联系人" width="100" />
            <el-table-column prop="phone" label="电话" width="120" />
            <el-table-column prop="service" label="需求类型" />
            <el-table-column prop="created_at" label="时间" width="100">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default>
                <el-button link type="primary">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统公告</span>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="(activity, index) in activities"
              :key="index"
              :type="activity.type"
              :timestamp="activity.time"
            >
              {{ activity.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { View, Briefcase, Document, Message, Plus, EditPen, Service } from '@element-plus/icons-vue'
import { getContactStats } from '@/api/contacts'

const stats = ref({
  cases: 12,
  news: 6,
  contacts: 0
})

const recentContacts = ref([
  { name: '张先生', phone: '138****8888', service: '网站建设', created_at: '2024-01-15' },
  { name: '李女士', phone: '139****6666', service: '小程序开发', created_at: '2024-01-14' },
  { name: '王经理', phone: '137****9999', service: 'APP开发', created_at: '2024-01-13' }
])

const activities = ref([
  { content: '系统初始化完成', time: '2024-01-15 10:00', type: 'primary' },
  { content: '新增案例：深圳市公安局官方网站', time: '2024-01-14 15:30', type: 'success' },
  { content: '发布新闻：荣获国家级高新技术企业认定', time: '2024-01-13 09:20', type: 'info' },
  { content: '收到新的客户咨询', time: '2024-01-12 16:45', type: 'warning' }
])

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

onMounted(async () => {
  try {
    const res = await getContactStats()
    stats.value.contacts = res.pending || 0
  } catch (error) {
    console.error(error)
  }
})
</script>

<style scoped lang="scss">
.dashboard {
  .stat-row {
    margin-bottom: 20px;
  }
  
  .stat-card {
    :deep(.el-card__body) {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    
    .stat-icon {
      width: 60px;
      height: 60px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 28px;
    }
    
    .stat-info {
      .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: #262626;
        line-height: 1;
      }
      
      .stat-label {
        font-size: 14px;
        color: #8c8c8c;
        margin-top: 8px;
      }
    }
  }
  
  .quick-actions {
    margin-bottom: 20px;
    
    .action-list {
      display: flex;
      gap: 24px;
      flex-wrap: wrap;
    }
    
    .action-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 16px 24px;
      border-radius: 12px;
      transition: all 0.3s;
      
      &:hover {
        background: #f5f7fa;
        transform: translateY(-2px);
      }
      
      .action-icon {
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
      }
      
      span {
        font-size: 14px;
        color: #595959;
      }
    }
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .el-row {
    margin-bottom: 20px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}
</style>
