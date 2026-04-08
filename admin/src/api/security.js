import request from '@/utils/request'

// 获取安全概览
export const getSecurityOverview = () => {
  return request.get('/security/overview')
}

// 获取操作日志
export const getLogs = (params) => {
  return request.get('/logs', { params })
}
