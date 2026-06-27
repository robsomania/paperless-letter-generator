from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.database import Base


class LaTeXTemplate(Base):
    __tablename__ = "latex_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    latex_source = Column(Text, nullable=False)
    variable_config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    letters = relationship("Letter", back_populates="template", cascade="all, delete-orphan")


class CorrespondentProfile(Base):
    __tablename__ = "correspondent_profiles"

    id = Column(Integer, primary_key=True, index=True)
    paperless_id = Column(Integer, unique=True, nullable=True)
    name = Column(String(255), nullable=False)
    salutation = Column(String(50), default="")
    company = Column(String(255), default="")
    street = Column(String(255), default="")
    zip_city = Column(String(255), default="")
    country = Column(String(255), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    letters = relationship("Letter", back_populates="correspondent_profile", foreign_keys="Letter.correspondent_profile_id")


class SenderProfile(Base):
    __tablename__ = "sender_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    street = Column(String(255), default="")
    zip_city = Column(String(255), default="")
    country = Column(String(255), default="")
    email = Column(String(255), default="")
    phone = Column(String(255), default="")
    is_default = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    letters = relationship("Letter", back_populates="sender_profile", foreign_keys="Letter.sender_profile_id")


class Letter(Base):
    __tablename__ = "letters"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("latex_templates.id"), nullable=False)
    correspondent_profile_id = Column(Integer, ForeignKey("correspondent_profiles.id"), nullable=True)
    sender_profile_id = Column(Integer, ForeignKey("sender_profiles.id"), nullable=True)
    source_document_id = Column(Integer, nullable=True)
    paperless_document_id = Column(String(255), nullable=True)
    version_group_id = Column(Integer, nullable=True)

    field_values = Column(JSON, default=dict)
    attachments = Column(JSON, default=list)
    attachment_watermark = Column(Boolean, default=True)
    status = Column(String(50), default="draft")
    pdf_path = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    template = relationship("LaTeXTemplate", back_populates="letters")
    correspondent_profile = relationship("CorrespondentProfile", back_populates="letters", foreign_keys=[correspondent_profile_id])
    sender_profile = relationship("SenderProfile", back_populates="letters", foreign_keys=[sender_profile_id])
