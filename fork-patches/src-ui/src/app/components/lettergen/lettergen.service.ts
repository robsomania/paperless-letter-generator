import { Injectable } from '@angular/core'
import { HttpClient, HttpParams } from '@angular/common/http'
import { Observable } from 'rxjs'

export interface LaTeXTemplate {
  id: number
  name: string
  description: string
  latex_source: string
  variable_config: Record<string, { label: string; type: string; required: boolean }>
  created_at: string
  updated_at: string
}

export interface DiscoveredVariable {
  name: string
  label: string
  type: string
  required: boolean
}

export interface CorrespondentProfile {
  id: number
  paperless: number
  paperless_id: number
  salutation: string
  company: string
  street: string
  zip_city: string
  country: string
  created_at: string
  updated_at: string
}

export interface Letter {
  id: number
  template: number
  template_name: string
  correspondent_profile: number | null
  correspondent: number | null
  correspondent_name: string | null
  source_document: number | null
  result_document: number | null
  field_values: Record<string, string>
  status: 'draft' | 'generated' | 'sent'
  pdf: string | null
  pdf_url: string | null
  created_at: string
  updated_at: string
}

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
}

@Injectable({ providedIn: 'root' })
export class LettergenService {
  private base = '/api'

  constructor(private http: HttpClient) {}

  // Templates
  getTemplates(): Observable<LaTeXTemplate[]> {
    return this.http.get<LaTeXTemplate[]>(`${this.base}/lettergen_templates/`)
  }
  getTemplate(id: number): Observable<LaTeXTemplate> {
    return this.http.get<LaTeXTemplate>(`${this.base}/lettergen_templates/${id}/`)
  }
  createTemplate(data: Partial<LaTeXTemplate>): Observable<LaTeXTemplate> {
    return this.http.post<LaTeXTemplate>(`${this.base}/lettergen_templates/`, data)
  }
  updateTemplate(id: number, data: Partial<LaTeXTemplate>): Observable<LaTeXTemplate> {
    return this.http.put<LaTeXTemplate>(`${this.base}/lettergen_templates/${id}/`, data)
  }
  deleteTemplate(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/lettergen_templates/${id}/`)
  }
  getTemplateVariables(id: number): Observable<DiscoveredVariable[]> {
    return this.http.get<DiscoveredVariable[]>(`${this.base}/lettergen_templates/${id}/variables/`)
  }
  previewTemplate(id: number, fieldValues: Record<string, string>): Observable<Blob> {
    return this.http.post(
      `${this.base}/lettergen_templates/${id}/preview/`,
      { field_values: fieldValues },
      { responseType: 'blob' },
    )
  }

  // Correspondent Profiles
  getProfiles(): Observable<CorrespondentProfile[]> {
    return this.http.get<CorrespondentProfile[]>(`${this.base}/lettergen_profiles/`)
  }
  getProfile(id: number): Observable<CorrespondentProfile> {
    return this.http.get<CorrespondentProfile>(`${this.base}/lettergen_profiles/${id}/`)
  }
  getProfileByPaperless(paperlessId: number): Observable<CorrespondentProfile> {
    return this.http.get<CorrespondentProfile>(`${this.base}/lettergen_profiles/by-paperless/${paperlessId}/`)
  }
  createProfile(data: Partial<CorrespondentProfile>): Observable<CorrespondentProfile> {
    return this.http.post<CorrespondentProfile>(`${this.base}/lettergen_profiles/`, data)
  }
  updateProfile(id: number, data: Partial<CorrespondentProfile>): Observable<CorrespondentProfile> {
    return this.http.put<CorrespondentProfile>(`${this.base}/lettergen_profiles/${id}/`, data)
  }
  deleteProfile(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/lettergen_profiles/${id}/`)
  }

  // Letters
  getLetters(): Observable<Letter[]> {
    return this.http.get<Letter[]>(`${this.base}/lettergen_letters/`)
  }
  getLetter(id: number): Observable<Letter> {
    return this.http.get<Letter>(`${this.base}/lettergen_letters/${id}/`)
  }
  createLetter(data: {
    template: number
    correspondent?: number | null
    field_values: Record<string, string>
  }): Observable<Letter> {
    return this.http.post<Letter>(`${this.base}/lettergen_letters/`, data)
  }
  generateLetter(id: number): Observable<Letter> {
    return this.http.post<Letter>(`${this.base}/lettergen_letters/${id}/generate/`, {})
  }
  sendLetter(id: number, data: { title?: string; tags?: number[] }): Observable<Letter> {
    return this.http.post<Letter>(`${this.base}/lettergen_letters/${id}/send/`, data)
  }
  getLetterPdf(id: number): Observable<Blob> {
    return this.http.get(`${this.base}/lettergen_letters/${id}/pdf/`, { responseType: 'blob' })
  }
  deleteLetter(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/lettergen_letters/${id}/`)
  }

  // Paperless API (proxied through DRF)
  getPaperlessCorrespondents(): Observable<PaperlessCorrespondent[]> {
    return this.http.get<PaperlessCorrespondent[]>(`${this.base}/correspondents/`)
  }
  getPaperlessDocument(id: number): Observable<PaperlessDocument> {
    return this.http.get<PaperlessDocument>(`${this.base}/documents/${id}/`)
  }
}
