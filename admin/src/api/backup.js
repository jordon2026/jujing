import request from '@/utils/request'

// 获取备份列表
export function getBackups() {
  return request({
    url: '/backup',
    method: 'get'
  })
}

// 创建备份
export function createBackup() {
  return request({
    url: '/backup',
    method: 'post'
  })
}

// 删除备份
export function deleteBackup(filename) {
  return request({
    url: `/backup/${filename}`,
    method: 'delete'
  })
}

// 恢复备份
export function restoreBackup(filename) {
  return request({
    url: `/backup/restore/${filename}`,
    method: 'post'
  })
}

// 下载备份
export function downloadBackup(filename) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
  const token = localStorage.getItem('token')
  const url = `${baseURL}/api/backup/download/${filename}?token=${token}`
  window.open(url, '_blank')
}
