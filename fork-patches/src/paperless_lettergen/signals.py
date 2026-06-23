from django.db.models.signals import post_migrate
from django.dispatch import receiver

from paperless_lettergen.models import LaTeXTemplate


@receiver(post_migrate)
def seed_default_templates(sender, **kwargs):
    if sender.name != "paperless_lettergen":
        return
    if LaTeXTemplate.objects.exists():
        return

    from pathlib import Path

    templates_dir = Path(__file__).parent / "default_templates"

    templates = [
        {
            "name": "Formeller Geschäftsbrief",
            "description": "Standard Geschäftsbrief nach DIN 5008 mit scrlttr2",
            "filename": "formal_business.tex",
            "variable_config": {
                "sender_name": {"label": "Absender Name", "type": "text", "required": True},
                "sender_street": {"label": "Straße", "type": "text", "required": True},
                "sender_zip_city": {"label": "PLZ Ort", "type": "text", "required": True},
                "sender_email": {"label": "E-Mail", "type": "text", "required": False},
                "sender_phone": {"label": "Telefon", "type": "text", "required": False},
                "recipient_name": {"label": "Empfänger Name", "type": "text", "required": True},
                "recipient_gender": {"label": "Anrede (e/r)", "type": "text", "required": False},
                "recipient_company": {"label": "Firma", "type": "text", "required": False},
                "recipient_street": {"label": "Straße", "type": "text", "required": True},
                "recipient_zip_city": {"label": "PLZ Ort", "type": "text", "required": True},
                "subject": {"label": "Betreff", "type": "text", "required": True},
                "place": {"label": "Ort", "type": "text", "required": False},
                "date": {"label": "Datum", "type": "date", "required": True},
                "body": {"label": "Text", "type": "textarea", "required": True},
            },
        },
        {
            "name": "Persönlicher Brief",
            "description": "Informeller persönlicher Brief",
            "filename": "personal.tex",
            "variable_config": {
                "sender_name": {"label": "Absender Name", "type": "text", "required": True},
                "sender_street": {"label": "Straße", "type": "text", "required": True},
                "sender_zip_city": {"label": "PLZ Ort", "type": "text", "required": True},
                "recipient_name": {"label": "Empfänger Name", "type": "text", "required": True},
                "recipient_gender": {"label": "Anrede (e/r)", "type": "text", "required": False},
                "recipient_street": {"label": "Straße", "type": "text", "required": True},
                "recipient_zip_city": {"label": "PLZ Ort", "type": "text", "required": True},
                "subject": {"label": "Betreff", "type": "text", "required": False},
                "place": {"label": "Ort", "type": "text", "required": False},
                "date": {"label": "Datum", "type": "date", "required": True},
                "body": {"label": "Text", "type": "textarea", "required": True},
                "closing": {"label": "Grußformel", "type": "text", "required": False},
            },
        },
    ]

    for tpl in templates:
        filepath = templates_dir / tpl["filename"]
        if filepath.exists():
            LaTeXTemplate.objects.create(
                name=tpl["name"],
                description=tpl["description"],
                latex_source=filepath.read_text(encoding="utf-8"),
                variable_config=tpl["variable_config"],
            )
