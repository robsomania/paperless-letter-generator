from django.db import models
from django.utils.translation import gettext_lazy as _

from documents.models import Correspondent, Document


class LaTeXTemplate(models.Model):
    name = models.CharField(_("name"), max_length=255)
    description = models.TextField(_("description"), blank=True, default="")
    latex_source = models.TextField(_("LaTeX source"))
    variable_config = models.JSONField(_("variable configuration"), default=dict, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("LaTeX template")
        verbose_name_plural = _("LaTeX templates")
        ordering = ("-updated_at",)

    def __str__(self):
        return self.name


class CorrespondentProfile(models.Model):
    paperless = models.OneToOneField(
        Correspondent,
        on_delete=models.CASCADE,
        related_name="lettergen_profile",
        verbose_name=_("correspondent"),
    )
    salutation = models.CharField(_("salutation"), max_length=50, blank=True, default="")
    company = models.CharField(_("company"), max_length=255, blank=True, default="")
    street = models.CharField(_("street"), max_length=255, blank=True, default="")
    zip_city = models.CharField(_("ZIP / city"), max_length=255, blank=True, default="")
    country = models.CharField(_("country"), max_length=255, blank=True, default="")
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("correspondent profile")
        verbose_name_plural = _("correspondent profiles")

    def __str__(self):
        return self.paperless.name


class Letter(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        GENERATED = "generated", _("Generated")
        SENT = "sent", _("Sent")

    template = models.ForeignKey(
        LaTeXTemplate,
        on_delete=models.CASCADE,
        related_name="letters",
        verbose_name=_("template"),
    )
    correspondent_profile = models.ForeignKey(
        CorrespondentProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("correspondent profile"),
    )
    correspondent = models.ForeignKey(
        Correspondent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("correspondent"),
    )
    source_document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("source document"),
    )
    result_document = models.ForeignKey(
        Document,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("result document"),
    )
    field_values = models.JSONField(_("field values"), default=dict, blank=True)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    pdf = models.FileField(_("PDF"), upload_to="lettergen/", null=True, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("letter")
        verbose_name_plural = _("letters")
        ordering = ("-created_at",)

    def __str__(self):
        return f"Letter #{self.pk} ({self.template.name})"
