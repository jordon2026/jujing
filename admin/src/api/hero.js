import request from '@/utils/request'

export const getHero = () => {
  return request.get('/hero')
}

export const updateHero = (data) => {
  return request.put('/hero', data)
}

export const getStats = () => {
  return request.get('/hero/stats')
}

export const updateStats = (data) => {
  return request.put('/hero/stats', data)
}
