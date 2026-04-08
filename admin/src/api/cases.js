import request from '@/utils/request'

export const getCases = (params) => {
  return request.get('/cases', { params })
}

export const createCase = (data) => {
  return request.post('/cases', data)
}

export const updateCase = (id, data) => {
  return request.put(`/cases/${id}`, data)
}

export const deleteCase = (id) => {
  return request.delete(`/cases/${id}`)
}

export const getCategories = () => {
  return request.get('/cases/categories')
}
