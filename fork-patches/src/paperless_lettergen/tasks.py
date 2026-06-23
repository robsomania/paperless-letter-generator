import json
import logging
import os
import shutil
import tempfile
from pathlib import Path

from django.conf import settings

from paperless_lettergen.models import Letter
from paperless_lettergen.services.latex import generate_pdf, LatexCompileError
from paperless_lettergen.services.template_vars import build_field_values

logger = logging.getLogger("paperless.lettergen.tasks")


def generate_letter_pdf(letter_id: int) -> str | None:
    try:
        letter = Letter.objects.select_related(
            "template", "correspondent_profile", "correspondent",
        ).get(pk=letter_id)
    except Letter.DoesNotExist:
        logger.error(f"Letter {letter_id} not found")
        return None

    values = build_field_values(letter)
    try:
        with tempfile.TemporaryDirectory(prefix="lettergen-") as tmp:
            pdf_path = generate_pdf(letter.template.latex_source, values, Path(tmp))
            pdf_name = f"letter_{letter_id}.pdf"
            dest = os.path.join(settings.MEDIA_ROOT, "lettergen", pdf_name)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(pdf_path, dest)
            logger.info(f"PDF generated for letter {letter_id}: {dest}")
            letter.status = Letter.Status.GENERATED
            letter.pdf.name = f"lettergen/{pdf_name}"
            letter.save(update_fields=["pdf", "status"])
            return dest
    except LatexCompileError as e:
        logger.error(f"LaTeX compilation failed for letter {letter_id}: {e}")
        return None


def send_letter_to_paperless(
    letter_id: int,
    title: str = "",
    tag_ids: list[int] | None = None,
) -> int | None:
    try:
        letter = Letter.objects.select_related("template").get(pk=letter_id)
    except Letter.DoesNotExist:
        logger.error(f"Letter {letter_id} not found")
        return None

    if letter.status != Letter.Status.GENERATED or not letter.pdf:
        if generate_letter_pdf(letter_id) is None:
            return None
        letter.refresh_from_db()

    if not letter.pdf or not letter.pdf.path or not os.path.exists(letter.pdf.path):
        logger.error(f"PDF for letter {letter_id} not found on disk")
        return None

    consumption_dir = getattr(settings, "CONSUMPTION_DIR", None)
    if not consumption_dir:
        logger.error("CONSUMPTION_DIR not configured")
        return None

    title = title or letter.field_values.get("subject", "") or f"Letter #{letter_id}"
    correspondent_id = letter.correspondent_id
    corr_name = None
    if correspondent_id:
        from documents.models import Correspondent
        try:
            corr = Correspondent.objects.get(pk=correspondent_id)
            corr_name = corr.name
        except Correspondent.DoesNotExist:
            pass

    pdf_dest = os.path.join(consumption_dir, f"letter_{letter_id}.pdf")
    shutil.copy2(letter.pdf.path, pdf_dest)

    metadata = {
        "title": title,
    }
    if corr_name:
        metadata["correspondent"] = corr_name
    if tag_ids:
        from documents.models import Tag
        tag_names = list(
            Tag.objects.filter(pk__in=tag_ids).values_list("name", flat=True)
        )
        if tag_names:
            metadata["tags"] = tag_names

    metadata_path = os.path.join(consumption_dir, f"letter_{letter_id}.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(
        f"Letter {letter_id} written to consumption folder: {pdf_dest} "
        f"(result document will be linked after consumption)"
    )

    letter.status = Letter.Status.SENT
    letter.save(update_fields=["status"])

    return None
