<template>
  <div class="settings-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
        </div>
      </template>
      
      <el-tabs v-model="activeTab">
        <el-tab-pane label="修改密码" name="password">
          <el-form :model="passwordForm" label-width="100px" style="max-width: 400px;">
            <el-form-item label="原密码">
              <el-input
                v-model="passwordForm.oldPassword"
                type="password"
                show-password
                placeholder="请输入原密码"
              />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input
                v-model="passwordForm.newPassword"
                type="password"
                show-password
                placeholder="请输入新密码（至少8位，包含大小写字母和数字）"
              />
              <div class="password-strength" v-if="passwordForm.newPassword">
                <div class="strength-bar">
                  <div 
                    class="strength-fill" 
                    :class="checkPasswordStrength(passwordForm.newPassword).strength"
                  ></div>
                </div>
                <span class="strength-text">
                  密码强度：{{ { weak: '弱', medium: '中', strong: '强' }[checkPasswordStrength(passwordForm.newPassword).strength] }}
                </span>
              </div>
            </el-form-item>
            <el-form-item label="确认密码">
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                show-password
                placeholder="请再次输入新密码"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="changePassword">保存修改</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="数据库备份" name="backup">
          <div class="backup-section">
            <div class="backup-actions">
              <el-button type="primary" :loading="backupLoading" @click="createBackup">
                <el-icon><Plus /></el-icon>
                立即备份
              </el-button>
              <el-button @click="refreshBackups">
                <el-icon><Refresh /></el-icon>
                刷新列表
              </el-button>
            </div>
            
            <el-table :data="backupList" v-loading="loading" style="margin-top: 20px;">
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column prop="filename" label="备份文件名" min-width="200" />
              <el-table-column prop="size" label="文件大小" width="120" />
              <el-table-column prop="created_at" label="备份时间" width="180" />
              <el-table-column label="操作" width="280" fixed="right">
                <template #default="{ row }">
                  <el-button type="success" link @click="restoreBackup(row)">
                    <el-icon><RefreshRight /></el-icon>
                    恢复
                  </el-button>
                  <el-button type="primary" link @click="downloadBackup(row)">
                    <el-icon><Download /></el-icon>
                    下载
                  </el-button>
                  <el-button type="danger" link @click="deleteBackupHandler(row)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            
            <el-empty v-if="!loading && backupList.length === 0" description="暂无备份文件" />
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="安全中心" name="security">
          <div class="security-section">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-statistic title="今日操作数" :value="securityStats.todayOperations" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="登录失败次数" :value="securityStats.failedLogins" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="被锁定IP数" :value="securityStats.lockedIPs" />
              </el-col>
              <el-col :span="6">
                <el-statistic title="总日志数" :value="securityStats.totalLogs" />
              </el-col>
            </el-row>
            
            <el-divider />
            
            <div class="security-config">
              <h4>安全策略配置</h4>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="登录失败锁定">连续 {{ 5 }} 次失败锁定 {{ 15 }} 分钟</el-descriptions-item>
                <el-descriptions-item label="请求频率限制">每 {{ securityStats.rateLimitWindow || 60 }} 秒最多 {{ securityStats.rateLimitMax || 100 }} 个请求</el-descriptions-item>
                <el-descriptions-item label="验证码有效期">5 分钟</el-descriptions-item>
                <el-descriptions-item label="Token有效期">8 小时</el-descriptions-item>
                <el-descriptions-item label="密码强度要求">至少8位，包含大小写字母和数字</el-descriptions-item>
              </el-descriptions>
            </div>
            
            <el-divider />
            
            <div class="locked-ips" v-if="securityStats.lockedIPList && securityStats.lockedIPList.length > 0">
              <h4>当前被锁定的IP</h4>
              <el-tag 
                v-for="ip in securityStats.lockedIPList" 
                :key="ip"
                type="danger"
                effect="dark"
                style="margin-right: 10px; margin-bottom: 10px;"
              >
                {{ ip }}
              </el-tag>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="操作日志" name="logs">
          <div class="logs-section">
            <el-table :data="logsList" v-loading="logsLoading" style="width: 100%">
              <el-table-column prop="id" label="ID" width="60" />
              <el-table-column prop="timestamp" label="时间" width="180" />
              <el-table-column prop="ip" label="IP地址" width="140" />
              <el-table-column prop="user" label="用户" width="100" />
              <el-table-column prop="action" label="操作类型" width="150">
                <template #default="{ row }">
                  <el-tag :type="getActionType(row.action)" size="small">
                    {{ row.action }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="target_type" label="操作对象" width="120" />
              <el-table-column prop="details" label="详情" show-overflow-tooltip />
            </el-table>
            
            <el-pagination
              v-model:current-page="logsPage"
              v-model:page-size="logsPageSize"
              :total="logsTotal"
              layout="total, prev, pager, next"
              style="margin-top: 20px; justify-content: flex-end;"
              @current-change="fetchLogs"
            />
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="系统信息" name="info">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="系统名称">聚景科技管理系统</el-descriptions-item>
            <el-descriptions-item label="版本号">v1.0.0</el-descriptions-item>
            <el-descriptions-item label="开发公司">北京聚景科技有限公司</el-descriptions-item>
            <el-descriptions-item label="技术支持">admin@jujingyun.com</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Delete, RefreshRight } from '@element-plus/icons-vue'
import { changePassword as changePasswordApi } from '@/api/auth'
import { getBackups, createBackup as createBackupApi, deleteBackup, downloadBackup as downloadBackupApi, restoreBackup as restoreBackupApi } from '@/api/backup'
import { getSecurityOverview, getLogs } from '@/api/security'

const activeTab = ref('password')
const loading = ref(false)
const backupLoading = ref(false)
const backupList = ref([])

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 安全统计
const securityStats = ref({
  todayOperations: 0,
  failedLogins: 0,
  lockedIPs: 0,
  totalLogs: 0,
  lockedIPList: [],
  rateLimitWindow: 60,
  rateLimitMax: 100
})

// 日志
const logsList = ref([])
const logsLoading = ref(false)
const logsPage = ref(1)
const logsPageSize = ref(20)
const logsTotal = ref(0)

// 密码强度检查
const checkPasswordStrength = (password) => {
  const checks = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password)
  }
  
  const passed = Object.values(checks).filter(Boolean).length
  let strength = 'weak'
  if (passed === 4) strength = 'strong'
  else if (passed >= 2) strength = 'medium'
  
  return { strength, checks }
}

const changePassword = async () => {
  if (!passwordForm.value.oldPassword || !passwordForm.value.newPassword) {
    ElMessage.warning('请填写完整信息')
    return
  }
  
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  
  // 密码强度验证
  const { strength, checks } = checkPasswordStrength(passwordForm.value.newPassword)
  if (strength === 'weak') {
    let msg = '密码强度不足，需要满足：'
    if (!checks.length) msg += '\n- 至少8位字符'
    if (!checks.uppercase) msg += '\n- 包含大写字母'
    if (!checks.lowercase) msg += '\n- 包含小写字母'
    if (!checks.number) msg += '\n- 包含数字'
    ElMessage.warning(msg)
    return
  }
  
  try {
    await changePasswordApi({
      oldPassword: passwordForm.value.oldPassword,
      newPassword: passwordForm.value.newPassword
    })
    ElMessage.success('密码修改成功')
    passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
  } catch (error) {
    console.error(error)
  }
}

// 获取备份列表
const fetchBackups = async () => {
  loading.value = true
  try {
    const res = await getBackups()
    backupList.value = res || []
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 创建备份
const createBackup = async () => {
  backupLoading.value = true
  try {
    await createBackupApi()
    ElMessage.success('备份创建成功')
    fetchBackups()
  } catch (error) {
    console.error(error)
  } finally {
    backupLoading.value = false
  }
}

// 刷新备份列表
const refreshBackups = () => {
  fetchBackups()
}

// 下载备份
const downloadBackup = (row) => {
  downloadBackupApi(row.filename)
}

// 恢复备份
const restoreBackup = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要从备份 "${row.filename}" 恢复数据吗？\n\n恢复前会自动创建当前数据的备份，恢复后将覆盖现有数据！`,
      '恢复备份',
      {
        confirmButtonText: '确定恢复',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    backupLoading.value = true
    const res = await restoreBackupApi(row.filename)
    
    if (res.pre_restore_backup) {
      ElMessage.success(`恢复成功！当前数据已备份为：${res.pre_restore_backup}`)
    } else {
      ElMessage.success('恢复成功！')
    }
    
    // 刷新备份列表
    fetchBackups()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error(error.response?.data?.message || '恢复失败')
    }
  } finally {
    backupLoading.value = false
  }
}

// 删除备份
const deleteBackupHandler = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该备份文件吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteBackup(row.filename)
    ElMessage.success('删除成功')
    fetchBackups()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

// 获取安全概览
const fetchSecurityOverview = async () => {
  try {
    const res = await getSecurityOverview()
    securityStats.value = res.data || res
  } catch (error) {
    console.error(error)
  }
}

// 获取操作日志
const fetchLogs = async () => {
  logsLoading.value = true
  try {
    const res = await getLogs({
      page: logsPage.value,
      pageSize: logsPageSize.value
    })
    logsList.value = res.data?.list || res.list || []
    logsTotal.value = res.data?.total || res.total || 0
  } catch (error) {
    console.error(error)
  } finally {
    logsLoading.value = false
  }
}

// 获取操作类型标签样式
const getActionType = (action) => {
  if (action.includes('delete')) return 'danger'
  if (action.includes('create')) return 'success'
  if (action.includes('update')) return 'warning'
  if (action.includes('login')) return 'primary'
  return 'info'
}

onMounted(() => {
  fetchBackups()
  fetchSecurityOverview()
  fetchLogs()
})
</script>

<style scoped lang="scss">
.settings-page {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .password-strength {
    margin-top: 8px;
    
    .strength-bar {
      width: 100%;
      height: 4px;
      background: #e4e7ed;
      border-radius: 2px;
      overflow: hidden;
      
      .strength-fill {
        height: 100%;
        transition: all 0.3s;
        
        &.weak {
          width: 33%;
          background: #f56c6c;
        }
        
        &.medium {
          width: 66%;
          background: #e6a23c;
        }
        
        &.strong {
          width: 100%;
          background: #67c23a;
        }
      }
    }
    
    .strength-text {
      display: block;
      margin-top: 4px;
      font-size: 12px;
      color: #909399;
    }
  }
  
  .security-section {
    .security-config {
      margin-top: 20px;
      
      h4 {
        margin-bottom: 16px;
        font-size: 16px;
        color: #303133;
      }
    }
    
    .locked-ips {
      margin-top: 20px;
      
      h4 {
        margin-bottom: 12px;
        font-size: 14px;
        color: #f56c6c;
      }
    }
  }
  
  .logs-section {
    .el-tag {
      text-transform: capitalize;
    }
  }
}
</style>
