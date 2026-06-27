from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class VariableConfig(BaseModel):
    label: str = ""
    type: str = "text"
    required: bool = False


class LaTeXTemplateCreate(BaseModel):
    name: str
    description: str = ""
    latex_source: str
    variable_config: dict[str, VariableConfig] = {}


class LaTeXTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    latex_source: Optional[str] = None
    variable_config: Optional[dict[str, VariableConfig]] = None


class LaTeXTemplateOut(BaseModel):
    id: int
    name: str
    description: str
    latex_source: str
    variable_config: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DiscoveredVariable(BaseModel):
    name: str
    label: str
    type: str
    required: bool


class CorrespondentProfileCreate(BaseModel):
    paperless_id: Optional[int] = None
    name: str
    salutation: str = ""
    company: str = ""
    street: str = ""
    zip_city: str = ""
    country: str = ""


class CorrespondentProfileUpdate(BaseModel):
    paperless_id: Optional[int] = None
    name: Optional[str] = None
    salutation: Optional[str] = None
    company: Optional[str] = None
    street: Optional[str] = None
    zip_city: Optional[str] = None
    country: Optional[str] = None


class CorrespondentProfileOut(BaseModel):
    id: int
    paperless_id: Optional[int]
    name: str
    salutation: str
    company: str
    street: str
    zip_city: str
    country: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SenderProfileCreate(BaseModel):
    name: str
    street: str = ""
    zip_city: str = ""
    country: str = ""
    email: str = ""
    phone: str = ""
    is_default: bool = False


class SenderProfileUpdate(BaseModel):
    name: Optional[str] = None
    street: Optional[str] = None
    zip_city: Optional[str] = None
    country: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_default: Optional[bool] = None


class SenderProfileOut(BaseModel):
    id: int
    name: str
    street: str
    zip_city: str
    country: str
    email: str
    phone: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AttachmentInfo(BaseModel):
    document_id: Optional[int] = None
    name: str


class LetterCreate(BaseModel):
    template_id: int
    correspondent_profile_id: Optional[int] = None
    sender_profile_id: Optional[int] = None
    source_document_id: Optional[int] = None
    field_values: dict[str, str] = {}
    version_group_id: Optional[int] = None
    attachments: list[AttachmentInfo] = []
    attachment_watermark: bool = True


class LetterUpdate(BaseModel):
    field_values: Optional[dict[str, str]] = None
    status: Optional[str] = None
    attachments: Optional[list[AttachmentInfo]] = None
    attachment_watermark: Optional[bool] = None


class LetterOut(BaseModel):
    id: int
    template_id: int
    template_name: str = ""
    correspondent_profile_id: Optional[int] = None
    correspondent_name: Optional[str] = None
    sender_profile_id: Optional[int] = None
    sender_name: Optional[str] = None
    source_document_id: Optional[int] = None
    paperless_document_id: Optional[str] = None
    version_group_id: Optional[int] = None
    field_values: dict
    attachments: list = []
    attachment_watermark: bool = False
    status: str
    pdf_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("paperless_document_id", mode="before")
    @classmethod
    def coerce_doc_id(cls, v):
        if v is None:
            return None
        return str(v)

    @field_validator("attachments", mode="before")
    @classmethod
    def coerce_attachments(cls, v):
        return v or []

    @field_validator("attachment_watermark", mode="before")
    @classmethod
    def coerce_attachment_watermark(cls, v):
        return v if v is not None else False


class PaperlessCorrespondent(BaseModel):
    id: int
    name: str
    last_correspondence: Optional[datetime] = None
    document_count: Optional[int] = None


class PaperlessDocument(BaseModel):
    id: int
    title: str
    correspondent: Optional[int] = None
    correspondent_name: Optional[str] = None
    created: datetime
    added: datetime
    tags: list[int] = []


class SendToPaperless(BaseModel):
    title: Optional[str] = None
    correspondent_id: Optional[int] = None
    document_type_id: Optional[int] = None
    tags: list[int] = []
