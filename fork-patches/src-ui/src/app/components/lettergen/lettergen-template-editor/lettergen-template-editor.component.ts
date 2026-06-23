import { Component, OnInit } from '@angular/core'
import { ActivatedRoute, Router } from '@angular/router'
import { LettergenService, LaTeXTemplate, DiscoveredVariable } from '../lettergen.service'

interface VariableRow {
  name: string
  label: string
  type: string
  required: boolean
}

@Component({
  selector: 'app-lettergen-template-editor',
  templateUrl: './lettergen-template-editor.component.html',
})
export class LettergenTemplateEditorComponent implements OnInit {
  isNew = true
  templateId: number | null = null
  name = ''
  description = ''
  latexSource = ''
  variables: VariableRow[] = []
  saving = false

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private service: LettergenService,
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id')
    if (id && id !== 'new') {
      this.isNew = false
      this.templateId = Number(id)
      this.service.getTemplate(this.templateId).subscribe({
        next: (t) => {
          this.name = t.name
          this.description = t.description
          this.latexSource = t.latex_source
          const cfg = t.variable_config || {}
          this.variables = Object.entries(cfg).map(([name, c]: [string, any]) => ({
            name,
            label: c.label || name,
            type: c.type || 'text',
            required: c.required || false,
          }))
        },
        error: () => this.router.navigate(['/lettergen/templates']),
      })
    }
  }

  onSourceChange(): void {
    const matches = this.latexSource.match(/\{\{\s*(\w+)\s*\}\}/g) || []
    const names = [...new Set(matches.map((m) => m.replace(/[\{\}\s]/g, '')))]
    for (const name of names) {
      if (!this.variables.find((v) => v.name === name)) {
        this.variables.push({ name, label: name, type: 'text', required: false })
      }
    }
  }

  save(): void {
    this.saving = true
    const variableConfig: Record<string, any> = {}
    for (const v of this.variables) {
      variableConfig[v.name] = { label: v.label, type: v.type, required: v.required }
    }
    const payload = {
      name: this.name,
      description: this.description,
      latex_source: this.latexSource,
      variable_config: variableConfig,
    }
    const obs = this.isNew
      ? this.service.createTemplate(payload)
      : this.service.updateTemplate(this.templateId!, payload)
    obs.subscribe({
      next: () => this.router.navigate(['/lettergen/templates']),
      error: (e) => alert('Fehler beim Speichern: ' + (e.error?.detail || e.message)),
      complete: () => (this.saving = false),
    })
  }
}
