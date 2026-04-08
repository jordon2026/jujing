import request from '@/utils/request'

export const getServices = () => {
  return request.get('/services')
}

export const createService = (data) => {
  return request.post('/services', data)
}

export const updateService = (id, data) => {
  return request.put(`/services/${id}`, data)
}

export const deleteService = (id) => {
  return request.delete(`/services/${id}`)
}
