import api from './client'

export interface AttachmentInfo {
  document_id: number | null
  name: string
}

export interface Letter {
  id: number
  template_id: number
  template_name: string
  correspondent_profile_id: number | null
  correspondent_name: string | null
  sender_profile_id: number | null
  sender_name: string | null
  source_document_id: number | null
  paperless_document_id: string | null
  version_group_id: number | null
  field_values: Record<string, string>
  attachments: AttachmentInfo[]
  attachment_watermark: boolean
  status: 'draft' | 'generated' | 'sent'
  pdf_path: string | null
  created_at: string
  updated_at: string
}

export const lettersApi = {
  list: () => api.get<Letter[]>('/letters'),
  get: (id: number) => api.get<Letter>(`/letters/${id}`),
  create: (data: {
    template_id: number
    correspondent_profile_id?: number | null
    sender_profile_id?: number | null
    source_document_id?: number | null
    field_values: Record<string, string>
    attachments?: AttachmentInfo[]
    attachment_watermark?: boolean
    version_group_id?: number | null
  }) => api.post<Letter>('/letters', data),
  update: (id: number, data: Partial<Letter>) => api.put<Letter>(`/letters/${id}`, data),
  generate: (id: number) => api.post<Letter>(`/letters/${id}/generate`),
  send: (id: number, data: {
    title?: string
    correspondent_id?: number
    document_type_id?: number
    tags?: number[]
  }) => api.post<Letter>(`/letters/${id}/send`, data),
  download: (id: number) => api.get(`/letters/${id}/pdf`, { responseType: 'blob' }),
  delete: (id: number) => api.delete(`/letters/${id}`),
}
