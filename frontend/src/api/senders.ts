import api from './client'

export interface SenderProfile {
  id: number
  name: string
  street: string
  zip_city: string
  country: string
  email: string
  phone: string
  is_default: boolean
  created_at: string
  updated_at: string
}

export const sendersApi = {
  list: () => api.get<SenderProfile[]>('/sender-profiles'),
  get: (id: number) => api.get<SenderProfile>(`/sender-profiles/${id}`),
  getDefault: () => api.get<SenderProfile>('/sender-profiles/default'),
  create: (data: Partial<SenderProfile>) => api.post<SenderProfile>('/sender-profiles', data),
  update: (id: number, data: Partial<SenderProfile>) => api.put<SenderProfile>(`/sender-profiles/${id}`, data),
  delete: (id: number) => api.delete(`/sender-profiles/${id}`),
}
