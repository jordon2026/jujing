import request from '@/utils/request'

export const getNews = (params) => {
  return request.get('/news', { params })
}

export const createNews = (data) => {
  return request.post('/news', data)
}

export const updateNews = (id, data) => {
  return request.put(`/news/${id}`, data)
}

export const deleteNews = (id) => {
  return request.delete(`/news/${id}`)
}
