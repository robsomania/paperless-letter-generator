import { Component, OnInit } from '@angular/core'
import { ActivatedRoute } from '@angular/router'
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser'
import {
  LettergenService,
  LaTeXTemplate,
  DiscoveredVariable,
  PaperlessCorrespondent,
  PaperlessDocument,
  CorrespondentProfile,
} from '../lettergen.service'

@Component({
  selector: 'app-lettergen-compose',
  templateUrl: './lettergen-compose.component.html',
})
export class LettergenComposeComponent implements OnInit {
  templates: LaTeXTemplate[] = []
  selectedTemplate: LaTeXTemplate | null = null
  correspondents: PaperlessCorrespondent[] = []
  selectedCorrespondent: PaperlessCorrespondent | null = null
  profile: CorrespondentProfile | null = null
  formFields: DiscoveredVariable[] = []
  fieldValues: Record<string, string> = {}
  sourceDocumentId: number | null = null
  sourceDoc: PaperlessDocument | null = null
  addressFormVisible = false
  letterId: number | null = null
  letterStatus: string = ''
  generating = false
  sending = false
  pdfUrl: SafeResourceUrl | null = null
  pdfError: string | null = null

  address = { salutation: '', company: '', street: '', zip_city: '', country: '' }

  constructor(
    private route: ActivatedRoute,
    private service: LettergenService,
    private sanitizer: DomSanitizer,
  ) {}

  ngOnInit(): void {
    this.service.getTemplates().subscribe((t) => (this.templates = t))
    this.service.getPaperlessCorrespondents().subscribe((c) => (this.correspondents = c))
    this.route.queryParams.subscribe((params) => {
      if (params['template']) {
        const id = Number(params['template'])
        this.service.getTemplate(id).subscribe((t) => {
          this.selectedTemplate = t
          this.onTemplateChange()
        })
      }
    })
  }

  onTemplateChange(): void {
    this.formFields = []
    this.fieldValues = {}
    this.pdfUrl = null
    this.pdfError = null
    this.letterStatus = ''
    this.letterId = null
    if (!this.selectedTemplate) return
    this.service.getTemplateVariables(this.selectedTemplate.id).subscribe((vars) => {
      this.formFields = vars
      for (const f of vars) this.fieldValues[f.name] = ''
    })
  }

  onCorrespondentChange(): void {
    this.profile = null
    this.addressFormVisible = false
    if (!this.selectedCorrespondent) return
    this.service.getProfileByPaperless(this.selectedCorrespondent.id).subscribe({
      next: (p) => {
        this.profile = p
        this.applyProfile()
      },
      error: () => (this.addressFormVisible = true),
    })
  }

  applyProfile(): void {
    if (!this.profile) return
    this.address.salutation = this.profile.salutation
    this.address.company = this.profile.company
    this.address.street = this.profile.street
    this.address.zip_city = this.profile.zip_city
    this.address.country = this.profile.country
    this.fieldValues['recipient_name'] = this.selectedCorrespondent?.name || ''
    this.fieldValues['recipient_gender'] = this.profile.salutation
    this.fieldValues['recipient_company'] = this.profile.company
    this.fieldValues['recipient_street'] = this.profile.street
    this.fieldValues['recipient_zip_city'] = this.profile.zip_city
    this.fieldValues['recipient_country'] = this.profile.country
  }

  saveAddress(): void {
    if (!this.selectedCorrespondent) return
    const payload = {
      paperless: this.selectedCorrespondent.id,
      salutation: this.address.salutation,
      company: this.address.company,
      street: this.address.street,
      zip_city: this.address.zip_city,
      country: this.address.country,
    }
    this.service.createProfile(payload).subscribe({
      next: (p) => {
        this.profile = p
        this.addressFormVisible = false
        this.applyProfile()
      },
      error: (e) => alert('Fehler beim Speichern: ' + (e.error?.detail || e.message)),
    })
  }

  fetchSourceDoc(): void {
    if (!this.sourceDocumentId) return
    this.service.getPaperlessDocument(this.sourceDocumentId).subscribe({
      next: (d) => {
        this.sourceDoc = d
        this.fieldValues['reference'] = `Ihr Schreiben vom ${new Date(d.created).toLocaleDateString('de-DE')}, Betreff: ${d.title}`
      },
      error: () => alert('Dokument nicht gefunden'),
    })
  }

  generatePdf(): void {
    if (!this.selectedTemplate) return
    this.generating = true
    this.pdfError = null
    this.pdfUrl = null
    const obs = this.letterId
      ? this.service.generateLetter(this.letterId)
      : this.service.createLetter({
          template: this.selectedTemplate.id,
          correspondent: this.selectedCorrespondent?.id,
          field_values: this.fieldValues,
        })
    obs.subscribe({
      next: (letter) => {
        this.letterId = letter.id
        this.letterStatus = letter.status
        this.service.getLetterPdf(letter.id).subscribe({
          next: (blob) => {
            const url = URL.createObjectURL(blob)
            this.pdfUrl = this.sanitizer.bypassSecurityTrustResourceUrl(url)
          },
        })
      },
      error: (e) => (this.pdfError = e.error?.detail || 'Fehler bei Generierung'),
      complete: () => (this.generating = false),
    })
  }

  sendToPaperless(): void {
    if (!this.letterId) return
    this.sending = true
    this.service
      .sendLetter(this.letterId, {
        title: this.fieldValues['subject'] || `Brief #${this.letterId}`,
      })
      .subscribe({
        next: () => {
          this.letterStatus = 'sent'
          alert('Brief wurde an Paperless gesendet!')
        },
        error: (e) => alert('Fehler: ' + (e.error?.detail || e.message)),
        complete: () => (this.sending = false),
      })
  }

  formatDate(d: string): string {
    return new Date(d).toLocaleDateString('de-DE')
  }
}
