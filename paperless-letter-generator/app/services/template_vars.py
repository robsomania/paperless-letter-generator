from app.models import CorrespondentProfile, SenderProfile
from app.schemas import VariableConfig

KNOWN_VARIABLES: dict[str, str] = {
    "sender_name": "Absender Name",
    "sender_street": "Straße",
    "sender_zip_city": "PLZ Ort",
    "sender_country": "Land",
    "recipient_name": "Empfänger Name",
    "recipient_first_name": "Vorname",
    "recipient_last_name": "Nachname",
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
    "sender_email": "E-Mail",
    "sender_phone": "Telefon",
    "closing": "Grußformel",
}

KNOWN_TYPES: dict[str, str] = {
    "body": "textarea",
    "date": "date",
    "subject": "text",
    "reference": "textarea",
}

KNOWN_REQUIRED: set[str] = {"recipient_name", "body", "date"}


def get_correspondent_vars(profile: CorrespondentProfile | None) -> dict[str, str]:
    if profile is None:
        return {}
    name_parts = profile.name.strip().split(maxsplit=1)
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    return {
        "recipient_name": profile.name,
        "recipient_first_name": first_name,
        "recipient_last_name": last_name,
        "recipient_company": profile.company,
        "recipient_street": profile.street,
        "recipient_zip_city": profile.zip_city,
        "recipient_country": profile.country,
        "recipient_gender": profile.salutation or "",
    }


def get_sender_vars(profile: SenderProfile | None) -> dict[str, str]:
    if profile is None:
        return {}
    return {
        "sender_name": profile.name,
        "sender_street": profile.street,
        "sender_zip_city": profile.zip_city,
        "sender_country": profile.country,
        "sender_email": profile.email,
        "sender_phone": profile.phone,
    }


def auto_config_for_variables(variables: list[str]) -> dict[str, VariableConfig]:
    config: dict[str, VariableConfig] = {}
    for var in variables:
        config[var] = VariableConfig(
            label=KNOWN_VARIABLES.get(var, var.replace("_", " ").title()),
            type=KNOWN_TYPES.get(var, "text"),
            required=var in KNOWN_REQUIRED,
        )
    return config


def get_known_variable_configs() -> dict[str, VariableConfig]:
    config: dict[str, VariableConfig] = {}
    for var in KNOWN_VARIABLES:
        config[var] = VariableConfig(
            label=KNOWN_VARIABLES[var],
            type=KNOWN_TYPES.get(var, "text"),
            required=var in KNOWN_REQUIRED,
        )
    return config
