import { Component, OnInit } from '@angular/core'
import { LettergenService, LaTeXTemplate } from '../lettergen.service'

@Component({
  selector: 'app-lettergen-template-list',
  templateUrl: './lettergen-template-list.component.html',
})
export class LettergenTemplateListComponent implements OnInit {
  templates: LaTeXTemplate[] = []

  constructor(private service: LettergenService) {}

  ngOnInit(): void {
    this.load()
  }

  load(): void {
    this.service.getTemplates().subscribe({
      next: (t) => (this.templates = t),
    })
  }

  confirmDelete(t: LaTeXTemplate): void {
    if (!confirm(`Template "${t.name}" wirklich löschen?`)) return
    this.service.deleteTemplate(t.id).subscribe({
      next: () => this.load(),
      error: () => alert('Löschen fehlgeschlagen'),
    })
  }
}
