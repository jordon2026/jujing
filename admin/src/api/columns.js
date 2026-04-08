import request from '@/utils/request'

// 获取栏目列表
export const getColumns = () => {
  return request.get('/columns')
}

// 创建栏目
export const createColumn = (data) => {
  return request.post('/columns', data)
}

// 更新栏目
export const updateColumn = (id, data) => {
  return request.put(`/columns/${id}`, data)
}

// 删除栏目
export const deleteColumn = (id) => {
  return request.delete(`/columns/${id}`)
}

// 切换栏目状态
export const toggleColumnStatus = (id) => {
  return request.post(`/columns/${id}/toggle`)
}

// 批量排序
export const sortColumns = (sortData) => {
  return request.post('/columns/sort', { sortData })
}
