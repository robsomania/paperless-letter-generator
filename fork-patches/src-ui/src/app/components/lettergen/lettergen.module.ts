import { NgModule } from '@angular/core'
import { CommonModule } from '@angular/common'
import { FormsModule, ReactiveFormsModule } from '@angular/forms'
import { HttpClientModule } from '@angular/common/http'
import { RouterModule } from '@angular/router'

import { LettergenDashboardComponent } from './lettergen-dashboard/lettergen-dashboard.component'
import { LettergenTemplateListComponent } from './lettergen-template-list/lettergen-template-list.component'
import { LettergenTemplateEditorComponent } from './lettergen-template-editor/lettergen-template-editor.component'
import { LettergenComposeComponent } from './lettergen-compose/lettergen-compose.component'
import { LettergenLetterListComponent } from './lettergen-letter-list/lettergen-letter-list.component'
import { LettergenCorrespondentProfilesComponent } from './lettergen-correspondent-profiles/lettergen-correspondent-profiles.component'

@NgModule({
  declarations: [
    LettergenDashboardComponent,
    LettergenTemplateListComponent,
    LettergenTemplateEditorComponent,
    LettergenComposeComponent,
    LettergenLetterListComponent,
    LettergenCorrespondentProfilesComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    HttpClientModule,
    RouterModule,
  ],
  exports: [
    LettergenDashboardComponent,
    LettergenTemplateListComponent,
    LettergenTemplateEditorComponent,
    LettergenComposeComponent,
    LettergenLetterListComponent,
    LettergenCorrespondentProfilesComponent,
  ],
})
export class LettergenModule {}
