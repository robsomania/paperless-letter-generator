import api from './client'

export interface PaperlessCorrespondent {
  id: number
  name: string
  last_correspondence: string | null
  document_count: number | null
}

export interface PaperlessDocument {
  id: number
  title: string
  correspondent: number | null
  correspondent_name: string | null
  created: string
  added: string
  tags: number[]
}

export interface PaperlessDocumentSearchResult {
  id: number
  title: string
  correspondent_name: string | null
  created: string
}

export const paperlessApi = {
  me: () => api.get('/paperless/me'),
  listCorrespondents: () => api.get<PaperlessCorrespondent[]>('/paperless/correspondents'),
  getDocument: (id: number) => api.get<PaperlessDocument>(`/paperless/documents/${id}`),
  getCorrespondent: (id: number) => api.get(`/paperless/correspondents/${id}`),
  searchDocuments: (query: string) =>
    api.get<PaperlessDocumentSearchResult[]>(`/paperless/documents/search?q=${encodeURIComponent(query)}`),
}
