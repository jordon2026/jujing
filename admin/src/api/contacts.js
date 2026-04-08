import request from '@/utils/request'

export const getContacts = (params) => {
  return request.get('/contacts', { params })
}

export const updateContactStatus = (id, status) => {
  return request.put(`/contacts/${id}/status`, { status })
}

export const deleteContact = (id) => {
  return request.delete(`/contacts/${id}`)
}

export const getContactStats = () => {
  return request.get('/contacts/stats')
}
