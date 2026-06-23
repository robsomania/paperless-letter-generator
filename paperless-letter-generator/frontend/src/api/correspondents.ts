import api from './client'

export interface CorrespondentProfile {
  id: number
  paperless_id: number | null
  name: string
  salutation: string
  company: string
  street: string
  zip_city: string
  country: string
  created_at: string
  updated_at: string
}

export const correspondentsApi = {
  list: () => api.get<CorrespondentProfile[]>('/correspondent-profiles'),
  get: (id: number) => api.get<CorrespondentProfile>(`/correspondent-profiles/${id}`),
  getByPaperless: (paperlessId: number) =>
    api.get<CorrespondentProfile>(`/correspondent-profiles/by-paperless/${paperlessId}`),
  create: (data: Partial<CorrespondentProfile>) =>
    api.post<CorrespondentProfile>('/correspondent-profiles', data),
  update: (id: number, data: Partial<CorrespondentProfile>) =>
    api.put<CorrespondentProfile>(`/correspondent-profiles/${id}`, data),
  delete: (id: number) => api.delete(`/correspondent-profiles/${id}`),
}
