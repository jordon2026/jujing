import request from '@/utils/request'

export const getAbout = () => {
  return request.get('/about')
}

export const updateAbout = (data) => {
  return request.put('/about', data)
}

export const getTimeline = () => {
  return request.get('/about/timeline')
}

export const createTimeline = (data) => {
  return request.post('/about/timeline', data)
}

export const updateTimeline = (id, data) => {
  return request.put(`/about/timeline/${id}`, data)
}

export const deleteTimeline = (id) => {
  return request.delete(`/about/timeline/${id}`)
}
