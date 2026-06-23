import { Component, OnInit } from '@angular/core'
import { LettergenService } from '../lettergen.service'

@Component({
  selector: 'app-lettergen-dashboard',
  templateUrl: './lettergen-dashboard.component.html',
})
export class LettergenDashboardComponent implements OnInit {
  templateCount = 0
  draftCount = 0
  sentCount = 0
  recentLetters: any[] = []

  constructor(private service: LettergenService) {}

  ngOnInit(): void {
    this.service.getTemplates().subscribe({
      next: (t) => (this.templateCount = t.length),
    })
    this.service.getLetters().subscribe({
      next: (l) => {
        this.recentLetters = l.slice(0, 10)
        this.draftCount = l.filter((x) => x.status === 'draft').length
        this.sentCount = l.filter((x) => x.status === 'sent').length
      },
    })
  }

  statusLabel(s: string): string {
    const labels: Record<string, string> = {
      draft: 'Entwurf',
      generated: 'Generiert',
      sent: 'Gesendet',
    }
    return labels[s] || s
  }

  formatDate(d: string): string {
    return new Date(d).toLocaleDateString('de-DE')
  }
}
