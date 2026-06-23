import api from './client'

export interface VariableConfig {
  label: string
  type: string
  required: boolean
}

export interface LaTeXTemplate {
  id: number
  name: string
  description: string
  latex_source: string
  variable_config: Record<string, VariableConfig>
  created_at: string
  updated_at: string
}

export interface DiscoveredVariable {
  name: string
  label: string
  type: string
  required: boolean
}

export const templatesApi = {
  list: () => api.get<LaTeXTemplate[]>('/templates'),
  get: (id: number) => api.get<LaTeXTemplate>(`/templates/${id}`),
  create: (data: Partial<LaTeXTemplate>) => api.post<LaTeXTemplate>('/templates', data),
  update: (id: number, data: Partial<LaTeXTemplate>) => api.put<LaTeXTemplate>(`/templates/${id}`, data),
  delete: (id: number) => api.delete(`/templates/${id}`),
  variables: (id: number) => api.get<DiscoveredVariable[]>(`/templates/${id}/variables`),
  preview: (id: number, values: Record<string, string>) =>
    api.post(`/templates/${id}/preview`, values, { responseType: 'blob' }),
  knownVariables: () => api.get<Record<string, VariableConfig>>('/known-variables'),
}
