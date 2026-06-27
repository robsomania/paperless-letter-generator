import logging
import re
import shutil
import tempfile
from io import BytesIO
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pypdf import PdfReader, PdfWriter
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import LaTeXTemplate, Letter
from app.schemas import LetterCreate, LetterOut, LetterUpdate, SendToPaperless
from app.services.latex import generate_pdf, LatexCompileError
from app.services.paperless_client import paperless_client
from app.services.template_vars import get_correspondent_vars, get_sender_vars


def _format_date(val: str) -> str:
    m = re.match(r"^\d{4}-\d{2}-\d{2}$", val)
    if m:
        parts = val.split("-")
        return f"{parts[2]}.{parts[1]}.{parts[0]}"
    return val

logger = logging.getLogger("paperless-letter-generator.letters")
router = APIRouter(prefix="/api/letters", tags=["letters"])


def _build_encl_text(attachments: list[dict], existing_text: str = "") -> str:
    """Merge structured attachments with manually typed anlagen text."""
    lines: list[str] = []
    if existing_text.strip():
        for part in existing_text.split(","):
            p = part.strip()
            if p:
                lines.append(p)
    for att in attachments:
        name = att.get("name", "").strip()
        if name:
            lines.append(name)
    return ", ".join(lines)


def _add_watermark_to_page(page, label: str):
    pw = float(page.mediabox.width)
    from pypdf.annotations import FreeText
    annot = FreeText(
        text=label,
        rect=(pw / 2 - 80, 20, pw / 2 + 80, 45),
        font="Helvetica",
        font_size="9pt",
        font_color="808080",
        border_color="808080",
        border_style="dashed",
        align="center",
    )
    page.add_annotation(annot)


def _download_attachment_pdf(doc_id: int) -> bytes:
    """Synchronously download a PDF from Paperless."""
    base = settings.paperless_api_url.rstrip("/")
    h = {"Accept": "application/json; version=6"}
    if settings.paperless_api_token:
        h["Authorization"] = f"Token {settings.paperless_api_token}"
    with httpx.Client(base_url=base, headers=h, timeout=30) as c:
        r = c.get(f"/api/documents/{doc_id}/download/")
        r.raise_for_status()
        return r.content


def _merge_attachment_pdfs(letter_pdf: Path, attachments: list[dict], use_watermark: bool) -> Path:
    """Download attachment PDFs from Paperless, merge with watermark option."""
    digital = [a for a in attachments if a.get("document_id")]
    if not digital:
        return letter_pdf

    writer = PdfWriter()
    reader = PdfReader(str(letter_pdf))
    for p in reader.pages:
        writer.add_page(p)

    for idx, att in enumerate(digital):
        doc_id = att["document_id"]
        try:
            pdf_bytes = _download_attachment_pdf(doc_id)
        except Exception as e:
            logger.warning("Failed to download doc %d: %s", doc_id, e)
            continue
        att_reader = PdfReader(BytesIO(pdf_bytes))
        for pno, page in enumerate(att_reader.pages):
            if use_watermark:
                label = f"Anlage {idx + 1}" + (f" (S. {pno + 1})" if len(att_reader.pages) > 1 else "")
                _add_watermark_to_page(page, label)
            writer.add_page(page)

    merged_path = letter_pdf.parent / f"{letter_pdf.stem}_merged.pdf"
    with open(merged_path, "wb") as f:
        writer.write(f)
    return merged_path


@router.get("", response_model=list[LetterOut])
def list_letters(db: Session = Depends(get_db)):
    letters = db.query(Letter).order_by(Letter.created_at.desc()).all()
    result: list[LetterOut] = []
    for letter in letters:
        out = LetterOut.model_validate(letter)
        out.template_name = letter.template.name if letter.template else ""
        if letter.correspondent_profile:
            out.correspondent_name = letter.correspondent_profile.name
        if letter.sender_profile:
            out.sender_name = letter.sender_profile.name
        result.append(out)
    return result


@router.post("", response_model=LetterOut, status_code=201)
def create_letter(body: LetterCreate, db: Session = Depends(get_db)):
    tmpl = db.query(LaTeXTemplate).filter(LaTeXTemplate.id == body.template_id).first()
    if not tmpl:
        raise HTTPException(404, "Template not found")
    letter = Letter(
        template_id=body.template_id,
        correspondent_profile_id=body.correspondent_profile_id,
        sender_profile_id=body.sender_profile_id,
        source_document_id=body.source_document_id,
        field_values=body.field_values,
        attachments=[a.model_dump() for a in body.attachments],
        attachment_watermark=body.attachment_watermark,
        version_group_id=body.version_group_id,
        status="draft",
    )
    db.add(letter)
    db.commit()
    db.refresh(letter)
    if not letter.version_group_id:
        letter.version_group_id = letter.id
        db.commit()
        db.refresh(letter)
    out = LetterOut.model_validate(letter)
    out.template_name = tmpl.name
    if letter.correspondent_profile:
        out.correspondent_name = letter.correspondent_profile.name
    if letter.sender_profile:
        out.sender_name = letter.sender_profile.name
    return out


@router.post("/{letter_id}/generate", response_model=LetterOut)
def generate_letter(letter_id: int, db: Session = Depends(get_db)):
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    if not letter:
        raise HTTPException(404, "Letter not found")
    tmpl = letter.template
    if not tmpl:
        raise HTTPException(400, "Template not found")
    values = dict(letter.field_values or {})
    corr_profile = letter.correspondent_profile
    if corr_profile:
        corr_vars = get_correspondent_vars(corr_profile)
        for k, v in corr_vars.items():
            values.setdefault(k, v)
    sender_profile = letter.sender_profile
    if sender_profile:
        sender_vars = get_sender_vars(sender_profile)
        for k, v in sender_vars.items():
            values.setdefault(k, v)
    if "date" in values:
        values["date"] = _format_date(values["date"])
    latex_source = tmpl.latex_source
    if values.pop("_foldmarks", None) != "true":
        latex_source = re.sub(r"(\\begin{document})", r"\\KOMAoptions{foldmarks=false}\n\1", latex_source)

    attachments = (letter.attachments or []) if hasattr(letter, "attachments") else []
    if attachments:
        encl_text = _build_encl_text(attachments, values.get("anlagen", ""))
        if encl_text:
            if "{{ anlagen }}" in latex_source or "{{anlagen}}" in latex_source:
                values["anlagen"] = encl_text
            else:
                latex_source = re.sub(
                    r"(\\end{letter})",
                    r"\\encl{" + encl_text.replace("\\", "\\\\").replace("}", "\\}").replace("{", "\\{") + r"}\n\1",
                    latex_source,
                )

    letter_dir = settings.pdfs_path / str(letter.id)
    try:
        pdf = generate_pdf(latex_source, values, letter_dir)
    except LatexCompileError as e:
        raise HTTPException(422, f"LaTeX compilation failed: {e}" + (f"\n\nLog:\n{e.log}" if e.log else ""))

    if attachments:
        try:
            pdf = _merge_attachment_pdfs(pdf, attachments, bool(letter.attachment_watermark))
        except Exception as e:
            logger.warning("Failed to merge attachment PDFs: %s", e)

    letter.status = "generated"
    letter.pdf_path = str(pdf)
    db.commit()
    db.refresh(letter)
    out = LetterOut.model_validate(letter)
    out.template_name = tmpl.name
    if letter.correspondent_profile:
        out.correspondent_name = letter.correspondent_profile.name
    if letter.sender_profile:
        out.sender_name = letter.sender_profile.name
    return out


@router.post("/{letter_id}/send", response_model=LetterOut)
async def send_to_paperless(letter_id: int, body: SendToPaperless, db: Session = Depends(get_db)):
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    if not letter:
        raise HTTPException(404, "Letter not found")
    if letter.status != "generated" or not letter.pdf_path:
        raise HTTPException(400, "Letter must be generated first")
    pdf_path = Path(letter.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(400, "PDF file not found, regenerate the letter")
    title = body.title or f"Letter #{letter.id}"
    try:
        doc_id = await paperless_client.post_document(
            pdf_path=str(pdf_path),
            title=title,
            correspondent_id=body.correspondent_id,
            document_type_id=body.document_type_id,
            tags=body.tags,
        )
    except Exception as e:
        raise HTTPException(502, f"Failed to send to Paperless: {e}")
    letter.paperless_document_id = str(doc_id)
    letter.status = "sent"
    db.commit()
    db.refresh(letter)
    out = LetterOut.model_validate(letter)
    out.template_name = letter.template.name if letter.template else ""
    if letter.correspondent_profile:
        out.correspondent_name = letter.correspondent_profile.name
    if letter.sender_profile:
        out.sender_name = letter.sender_profile.name
    return out


@router.get("/{letter_id}", response_model=LetterOut)
def get_letter(letter_id: int, db: Session = Depends(get_db)):
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    if not letter:
        raise HTTPException(404, "Letter not found")
    out = LetterOut.model_validate(letter)
    out.template_name = letter.template.name if letter.template else ""
    if letter.correspondent_profile:
        out.correspondent_name = letter.correspondent_profile.name
    if letter.sender_profile:
        out.sender_name = letter.sender_profile.name
    return out


@router.put("/{letter_id}", response_model=LetterOut)
def update_letter(letter_id: int, body: LetterUpdate, db: Session = Depends(get_db)):
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    if not letter:
        raise HTTPException(404, "Letter not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(letter, field, value)
    db.commit()
    db.refresh(letter)
    out = LetterOut.model_validate(letter)
    out.template_name = letter.template.name if letter.template else ""
    if letter.correspondent_profile:
        out.correspondent_name = letter.correspondent_profile.name
    if letter.sender_profile:
        out.sender_name = letter.sender_profile.name
    return out


@router.delete("/{letter_id}", status_code=204)
def delete_letter(letter_id: int, db: Session = Depends(get_db)):
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    if not letter:
        raise HTTPException(404, "Letter not found")
    if letter.pdf_path:
        pdf = Path(letter.pdf_path)
        if pdf.exists():
            pdf.unlink()
    db.delete(letter)
    db.commit()


@router.get("/{letter_id}/pdf")
def download_pdf(letter_id: int, db: Session = Depends(get_db)):
    letter = db.query(Letter).filter(Letter.id == letter_id).first()
    if not letter:
        raise HTTPException(404, "Letter not found")
    if not letter.pdf_path:
        raise HTTPException(400, "PDF not yet generated")
    pdf = Path(letter.pdf_path)
    if not pdf.exists():
        raise HTTPException(404, "PDF file not found on disk")
    return FileResponse(str(pdf), media_type="application/pdf", filename=f"letter-{letter.id}.pdf")
