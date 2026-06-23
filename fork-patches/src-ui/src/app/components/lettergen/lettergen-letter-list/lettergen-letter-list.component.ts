import { Component, OnInit } from '@angular/core'
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser'
import { LettergenService, Letter } from '../lettergen.service'

@Component({
  selector: 'app-lettergen-letter-list',
  templateUrl: './lettergen-letter-list.component.html',
})
export class LettergenLetterListComponent implements OnInit {
  letters: Letter[] = []
  previewUrl: SafeResourceUrl | null = null

  constructor(
    private service: LettergenService,
    private sanitizer: DomSanitizer,
  ) {}

  ngOnInit(): void {
    this.load()
  }

  load(): void {
    this.service.getLetters().subscribe((l) => (this.letters = l))
  }

  statusLabel(s: string): string {
    const labels: Record<string, string> = { draft: 'Entwurf', generated: 'Generiert', sent: 'Gesendet' }
    return labels[s] || s
  }

  formatDate(d: string): string {
    return new Date(d).toLocaleDateString('de-DE')
  }

  regenerate(id: number): void {
    this.service.generateLetter(id).subscribe({
      next: () => this.load(),
      error: (e) => alert('Fehler: ' + (e.error?.detail || e.message)),
    })
  }

  downloadPdf(id: number): void {
    this.service.getLetterPdf(id).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `letter-${id}.pdf`
        a.click()
      },
    })
  }

  sendLetter(id: number): void {
    this.service.sendLetter(id, { title: `Brief #${id}` }).subscribe({
      next: () => {
        this.load()
        alert('Brief gesendet!')
      },
      error: (e) => alert('Fehler: ' + (e.error?.detail || e.message)),
    })
  }

  deleteLetter(id: number): void {
    if (!confirm('Brief wirklich löschen?')) return
    this.service.deleteLetter(id).subscribe({
      next: () => this.load(),
      error: () => alert('Löschen fehlgeschlagen'),
    })
  }
}
