import { Component, OnInit } from '@angular/core'
import { LettergenService, PaperlessCorrespondent, CorrespondentProfile } from '../lettergen.service'

@Component({
  selector: 'app-lettergen-correspondent-profiles',
  templateUrl: './lettergen-correspondent-profiles.component.html',
})
export class LettergenCorrespondentProfilesComponent implements OnInit {
  paperlessCorrespondents: PaperlessCorrespondent[] = []
  localProfiles: CorrespondentProfile[] = []
  selectedPaperlessId: number | null = null
  editingCorrespondent: PaperlessCorrespondent | null = null
  editingLocalId: number | null = null

  form = { salutation: '', company: '', street: '', zip_city: '', country: '' }
  loading = true

  constructor(private service: LettergenService) {}

  ngOnInit(): void {
    this.service.getPaperlessCorrespondents().subscribe({
      next: (c) => (this.paperlessCorrespondents = c),
    })
    this.service.getProfiles().subscribe({
      next: (p) => (this.localProfiles = p),
      complete: () => (this.loading = false),
    })
  }

  onSelect(): void {
    this.editingLocalId = null
    this.editingCorrespondent = null
    this.form = { salutation: '', company: '', street: '', zip_city: '', country: '' }
    if (!this.selectedPaperlessId) return
    const c = this.paperlessCorrespondents.find((x) => x.id === this.selectedPaperlessId)
    if (!c) return
    this.editingCorrespondent = c
    const existing = this.localProfiles.find((p) => p.paperless_id === c.id)
    if (existing) {
      this.editingLocalId = existing.id
      this.form = {
        salutation: existing.salutation,
        company: existing.company,
        street: existing.street,
        zip_city: existing.zip_city,
        country: existing.country,
      }
    }
  }

  save(): void {
    if (!this.editingCorrespondent) return
    const payload = { ...this.form, paperless: this.editingCorrespondent.id }
    const obs = this.editingLocalId
      ? this.service.updateProfile(this.editingLocalId, payload)
      : this.service.createProfile(payload)
    obs.subscribe({
      next: (p) => {
        const idx = this.localProfiles.findIndex((x) => x.id === p.id)
        if (idx !== -1) this.localProfiles[idx] = p
        else this.localProfiles.push(p)
      },
      error: (e) => alert('Fehler: ' + (e.error?.detail || e.message)),
    })
  }

  remove(): void {
    if (!this.editingLocalId || !confirm('Adresse löschen?')) return
    this.service.deleteProfile(this.editingLocalId).subscribe({
      next: () => {
        this.localProfiles = this.localProfiles.filter((p) => p.id !== this.editingLocalId)
        this.editingLocalId = null
        this.editingCorrespondent = null
        this.form = { salutation: '', company: '', street: '', zip_city: '', country: '' }
        this.selectedPaperlessId = null
      },
      error: () => alert('Löschen fehlgeschlagen'),
    })
  }

  editProfile(p: CorrespondentProfile): void {
    this.selectedPaperlessId = p.paperless_id
    this.onSelect()
  }
}
