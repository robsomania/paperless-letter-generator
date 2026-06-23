from documents.models import Correspondent
from paperless_lettergen.models import Letter


def get_correspondent_vars(letter: Letter) -> dict[str, str]:
    profile = letter.correspondent_profile
    corr = letter.correspondent
    if profile is None and corr is not None:
        try:
            profile = corr.lettergen_profile
        except Correspondent.lettergen_profile.RelatedObjectDoesNotExist:
            profile = None

    if profile is None:
        return {}

    corr_name = (
        profile.paperless.name
        if hasattr(profile, "paperless") and profile.paperless
        else (corr.name if corr else "")
    )
    return {
        "recipient_name": corr_name,
        "recipient_company": profile.company,
        "recipient_street": profile.street,
        "recipient_zip_city": profile.zip_city,
        "recipient_country": profile.country,
        "recipient_gender": profile.salutation or "",
    }


def build_field_values(letter: Letter) -> dict[str, str]:
    values = dict(letter.field_values or {})
    corr_vars = get_correspondent_vars(letter)
    for k, v in corr_vars.items():
        values.setdefault(k, v)
    return values


def auto_config_for_variables(variables: list[str]) -> dict[str, dict]:
    labels: dict[str, str] = {
        "sender_name": "Absender Name",
        "sender_street": "Straße",
        "sender_zip_city": "PLZ Ort",
        "sender_country": "Land",
        "sender_email": "E-Mail",
        "sender_phone": "Telefon",
        "recipient_name": "Empfänger Name",
        "recipient_gender": "Anrede (e/r)",
        "recipient_company": "Firma",
        "recipient_street": "Straße",
        "recipient_zip_city": "PLZ Ort",
        "recipient_country": "Land",
        "subject": "Betreff",
        "body": "Text",
        "date": "Datum",
        "place": "Ort",
        "reference": "Bezug",
        "signature": "Unterschrift",
        "closing": "Grußformel",
    }
    types: dict[str, str] = {
        "body": "textarea",
        "date": "date",
        "subject": "text",
        "reference": "textarea",
    }
    required: set[str] = {"recipient_name", "body", "date"}

    config: dict[str, dict] = {}
    for var in variables:
        config[var] = {
            "label": labels.get(var, var.replace("_", " ").title()),
            "type": types.get(var, "text"),
            "required": var in required,
        }
    return config
