import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LaTeXTemplate
from app.schemas import (
    LaTeXTemplateCreate,
    LaTeXTemplateOut,
    LaTeXTemplateUpdate,
    DiscoveredVariable,
    VariableConfig,
)
from app.services.latex import discover_variables, generate_pdf, LatexCompileError
from app.services.template_vars import auto_config_for_variables

logger = logging.getLogger("paperless-letter-generator.templates")
router = APIRouter(prefix="/api/templates", tags=["templates"])


@router.get("", response_model=list[LaTeXTemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return db.query(LaTeXTemplate).order_by(LaTeXTemplate.updated_at.desc()).all()


@router.post("", response_model=LaTeXTemplateOut, status_code=201)
def create_template(body: LaTeXTemplateCreate, db: Session = Depends(get_db)):
    if not body.latex_source.strip():
        raise HTTPException(422, "latex_source must not be empty")
    if not body.variable_config:
        variables = discover_variables(body.latex_source)
        body.variable_config = {k: VariableConfig() for k in variables}
    tmpl = LaTeXTemplate(
        name=body.name,
        description=body.description,
        latex_source=body.latex_source,
        variable_config={k: v.model_dump() for k, v in body.variable_config.items()},
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return tmpl


@router.get("/{template_id}", response_model=LaTeXTemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    tmpl = db.query(LaTeXTemplate).filter(LaTeXTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(404, "Template not found")
    return tmpl


@router.put("/{template_id}", response_model=LaTeXTemplateOut)
def update_template(template_id: int, body: LaTeXTemplateUpdate, db: Session = Depends(get_db)):
    tmpl = db.query(LaTeXTemplate).filter(LaTeXTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(404, "Template not found")
    if body.name is not None:
        tmpl.name = body.name
    if body.description is not None:
        tmpl.description = body.description
    if body.latex_source is not None:
        tmpl.latex_source = body.latex_source
    if body.variable_config is not None:
        tmpl.variable_config = {k: v.model_dump() for k, v in body.variable_config.items()}
    db.commit()
    db.refresh(tmpl)
    return tmpl


@router.delete("/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    tmpl = db.query(LaTeXTemplate).filter(LaTeXTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(404, "Template not found")
    db.delete(tmpl)
    db.commit()


@router.get("/{template_id}/variables", response_model=list[DiscoveredVariable])
def get_variables(template_id: int, db: Session = Depends(get_db)):
    tmpl = db.query(LaTeXTemplate).filter(LaTeXTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(404, "Template not found")
    variables = discover_variables(tmpl.latex_source)
    cfg = auto_config_for_variables(variables)
    existing = tmpl.variable_config or {}
    result: list[DiscoveredVariable] = []
    for var in variables:
        if var in existing:
            c = existing[var]
            result.append(DiscoveredVariable(
                name=var,
                label=c.get("label", var),
                type=c.get("type", "text"),
                required=c.get("required", False),
            ))
        elif var in cfg:
            c = cfg[var]
            result.append(DiscoveredVariable(
                name=var,
                label=c.label,
                type=c.type,
                required=c.required,
            ))
        else:
            result.append(DiscoveredVariable(name=var, label=var, type="text", required=False))
    return result


@router.post("/{template_id}/preview")
async def preview_template(template_id: int, field_values: dict[str, str], db: Session = Depends(get_db)):
    tmpl = db.query(LaTeXTemplate).filter(LaTeXTemplate.id == template_id).first()
    if not tmpl:
        raise HTTPException(404, "Template not found")
    try:
        with tempfile.TemporaryDirectory(prefix="letter-preview-") as tmp:
            pdf = generate_pdf(tmpl.latex_source, field_values, Path(tmp))
            from fastapi.responses import FileResponse
            return FileResponse(str(pdf), media_type="application/pdf", filename="preview.pdf")
    except LatexCompileError as e:
        raise HTTPException(422, f"LaTeX error: {e}" + (f"\n\nLog:\n{e.log}" if e.log else ""))
