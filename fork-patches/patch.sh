#!/usr/bin/env bash
# patch.sh -- Applies the Paperless Letter Generator to a paperless-ngx v2.20.x checkout
#
# Usage:
#   cd /path/to/paperless-ngx
#   bash /path/to/patch.sh
#
# For first-time setup, the script attempts automatic modifications.
# If any step fails, it provides manual instructions.
set -euo pipefail

PAPERLESS_DIR="$(pwd)"
PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Paperless Letter Generator — Fork Patch ==="
echo "Target: $PAPERLESS_DIR"
echo "Source: $PATCH_DIR"
echo ""

# --- Helper ---
try_patch() {
  if "$@"; then
    echo "  OK"
  else
    echo "  SKIPPED (manual step required)"
  fi
}

# --------------------------------------------------
# 1. Copy new Django app
# --------------------------------------------------
echo "[1/6] Installing Django app: paperless_lettergen"
mkdir -p "$PAPERLESS_DIR/src/paperless_lettergen"/{services,default_templates,migrations}

for f in __init__.py apps.py models.py serialisers.py views.py urls.py tasks.py signals.py; do
  cp "$PATCH_DIR/src/paperless_lettergen/$f" "$PAPERLESS_DIR/src/paperless_lettergen/$f"
done
for f in __init__.py latex.py template_vars.py; do
  cp "$PATCH_DIR/src/paperless_lettergen/services/$f" "$PAPERLESS_DIR/src/paperless_lettergen/services/$f"
done
for f in formal_business.tex personal.tex; do
  cp "$PATCH_DIR/src/paperless_lettergen/default_templates/$f" "$PAPERLESS_DIR/src/paperless_lettergen/default_templates/$f"
done
for f in __init__.py 0001_initial.py; do
  cp "$PATCH_DIR/src/paperless_lettergen/migrations/$f" "$PAPERLESS_DIR/src/paperless_lettergen/migrations/$f"
done
echo "  Done"

# --------------------------------------------------
# 2. Copy Angular frontend
# --------------------------------------------------
echo "[2/6] Installing Angular module: lettergen"
mkdir -p "$PAPERLESS_DIR/src-ui/src/app/components/lettergen"
mkdir -p "$PAPERLESS_DIR/src-ui/src/app/components/lettergen"/{lettergen-dashboard,lettergen-template-list,lettergen-template-editor,lettergen-compose,lettergen-letter-list,lettergen-correspondent-profiles}

cp "$PATCH_DIR/src-ui/src/app/components/lettergen/lettergen.module.ts" \
   "$PAPERLESS_DIR/src-ui/src/app/components/lettergen/lettergen.module.ts"
cp "$PATCH_DIR/src-ui/src/app/components/lettergen/lettergen.service.ts" \
   "$PAPERLESS_DIR/src-ui/src/app/components/lettergen/lettergen.service.ts"

for comp in lettergen-dashboard lettergen-template-list lettergen-template-editor \
            lettergen-compose lettergen-letter-list lettergen-correspondent-profiles; do
  cp "$PATCH_DIR/src-ui/src/app/components/lettergen/$comp/$comp.component.ts" \
     "$PAPERLESS_DIR/src-ui/src/app/components/lettergen/$comp/$comp.component.ts"
  cp "$PATCH_DIR/src-ui/src/app/components/lettergen/$comp/$comp.component.html" \
     "$PAPERLESS_DIR/src-ui/src/app/components/lettergen/$comp/$comp.component.html"
done
echo "  Done"

# --------------------------------------------------
# 3. INSTALLED_APPS
# --------------------------------------------------
echo "[3/6] Modifying INSTALLED_APPS..."
SETTINGS="$PAPERLESS_DIR/src/paperless/settings/__init__.py"
if grep -q "paperless_lettergen" "$SETTINGS"; then
  echo "  Already patched"
else
  # Insert after paperless_mail entry
  if grep -q "paperless_mail.apps.PaperlessMailConfig" "$SETTINGS"; then
    sed -i 's/paperless_mail.apps.PaperlessMailConfig/paperless_mail.apps.PaperlessMailConfig\n    "paperless_lettergen.apps.PaperlessLettergenConfig"/' "$SETTINGS"
    echo "  OK"
  else
    echo "  MANUAL: Add \"paperless_lettergen.apps.PaperlessLettergenConfig\" to INSTALLED_APPS in $SETTINGS"
  fi
fi

# --------------------------------------------------
# 4. API URLs
# --------------------------------------------------
echo "[4/6] Modifying API URLs..."
URLS="$PAPERLESS_DIR/src/paperless/urls.py"
if grep -q "lettergen" "$URLS"; then
  echo "  Already patched"
else
  # Add imports after last paperless_mail import
  IMPORTS_ADDED=false
  if grep -q "from paperless_mail" "$URLS"; then
    sed -i '/^from paperless_mail/a from paperless_lettergen.views import LaTeXTemplateViewSet, CorrespondentProfileViewSet, LetterViewSet' "$URLS"
    IMPORTS_ADDED=true
  fi

  # Register routers before the first api_router.register
  if grep -q "api_router.register" "$URLS"; then
    ROUTES='api_router.register(r"lettergen_templates", LaTeXTemplateViewSet, basename="lettergen_template")\napi_router.register(r"lettergen_profiles", CorrespondentProfileViewSet, basename="lettergen_profile")\napi_router.register(r"lettergen_letters", LetterViewSet, basename="lettergen_letter")'
    sed -i "0,/api_router.register/ s/api_router.register/$ROUTES\n&/" "$URLS"
    echo "  OK"
  elif $IMPORTS_ADDED; then
    echo "  MANUAL: Add api_router.register entries for lettergen_templates, lettergen_profiles, lettergen_letters"
  fi
fi

# --------------------------------------------------
# 5. Angular routing
# --------------------------------------------------
echo "[5/6] Modifying Angular routing..."
ROUTING="$PAPERLESS_DIR/src-ui/src/app/app-routing.module.ts"
if grep -q "lettergen" "$ROUTING"; then
  echo "  Already patched"
else
  echo "  MANUAL: Add to $ROUTING:"
  echo ""
  echo "  (a) Add imports at top:"
  echo "    import { LettergenDashboardComponent } from './components/lettergen/lettergen-dashboard/lettergen-dashboard.component'"
  echo "    import { LettergenTemplateListComponent } from './components/lettergen/lettergen-template-list/lettergen-template-list.component'"
  echo "    import { LettergenTemplateEditorComponent } from './components/lettergen/lettergen-template-editor/lettergen-template-editor.component'"
  echo "    import { LettergenComposeComponent } from './components/lettergen/lettergen-compose/lettergen-compose.component'"
  echo "    import { LettergenLetterListComponent } from './components/lettergen/lettergen-letter-list/lettergen-letter-list.component'"
  echo "    import { LettergenCorrespondentProfilesComponent } from './components/lettergen/lettergen-correspondent-profiles/lettergen-correspondent-profiles.component'"
  echo ""
  echo "  (b) Add routes inside the children array:"
  echo "    { path: 'lettergen', component: LettergenDashboardComponent, ... },"
  echo "    { path: 'lettergen/templates', component: LettergenTemplateListComponent, ... },"
  echo "    { path: 'lettergen/templates/new', component: LettergenTemplateEditorComponent, ... },"
  echo "    { path: 'lettergen/templates/:id', component: LettergenTemplateEditorComponent, ... },"
  echo "    { path: 'lettergen/compose', component: LettergenComposeComponent, ... },"
  echo "    { path: 'lettergen/letters', component: LettergenLetterListComponent, ... },"
  echo "    { path: 'lettergen/correspondents', component: LettergenCorrespondentProfilesComponent, ... },"
  echo ""
fi

# --------------------------------------------------
# 6. Sidebar navigation
# --------------------------------------------------
echo "[6/6] Modifying sidebar..."
NAV="$PAPERLESS_DIR/src-ui/src/app/components/app-frame/app-frame.component.html"
if grep -q "lettergen" "$NAV"; then
  echo "  Already patched"
else
  echo "  MANUAL: Add to $NAV (in the Manage section, after Mail nav item):"
  echo ""
  echo '    <li class="nav-item app-link">'
  echo '      <a class="nav-link" routerLink="lettergen" routerLinkActive="active" (click)="closeMenu()">'
  echo '        <i-bs class="me-2" name="envelope-paper"></i-bs>'
  echo '        <span><ng-container i18n>Letter Generator</ng-container></span>'
  echo '      </a>'
  echo '    </li>'
  echo ""
fi

# --------------------------------------------------
# 7. Dockerfile
# --------------------------------------------------
echo "[7/7] Modifying Dockerfile..."
DOCKERFILE="$PAPERLESS_DIR/Dockerfile"
if [ -f "$DOCKERFILE" ] && ! grep -q "texlive" "$DOCKERFILE" 2>/dev/null; then
  echo "  MANUAL: Add texlive packages to RUNTIME_PACKAGES in Dockerfile:"
  echo "    texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-lang-german"
  echo ""
else
  echo "  Skipped (no Dockerfile or already has texlive)"
fi

# --------------------------------------------------
echo ""
echo "=== Patch files copied. ==="
echo ""
echo "Manual steps required for Angular routing + sidebar + Dockerfile."
echo "See instructions above or run the Python check script."
echo ""
echo "After all modifications:"
echo "  python3 src/manage.py makemigrations paperless_lettergen"
echo "  python3 src/manage.py migrate"
echo "  cd src-ui && pnpm install && ng build --configuration production"
echo ""
echo "If using Docker:"
echo "  docker build -t paperless-ngx-lettergen ."
echo ""
echo "Default templates auto-seed on first migrate."
