import logging
import tempfile
from pathlib import Path

from django.http import FileResponse, Http404
from django.utils.translation import gettext_lazy as _

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from paperless_lettergen.models import LaTeXTemplate, CorrespondentProfile, Letter
from paperless_lettergen.serialisers import (
    LaTeXTemplateSerializer,
    CorrespondentProfileSerializer,
    CorrespondentProfileWriteSerializer,
    LetterSerializer,
    LetterWriteSerializer,
    DiscoveredVariableSerializer,
    SendToPaperlessSerializer,
)
from paperless_lettergen.services.latex import (
    discover_variables,
    generate_pdf,
    LatexCompileError,
)
from paperless_lettergen.services.template_vars import (
    auto_config_for_variables,
    build_field_values,
)
from paperless_lettergen import tasks

logger = logging.getLogger("paperless.lettergen.views")


class LaTeXTemplateViewSet(viewsets.ModelViewSet):
    queryset = LaTeXTemplate.objects.all()
    serializer_class = LaTeXTemplateSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=True, methods=["get"])
    def variables(self, request, pk=None):
        tmpl = self.get_object()
        discovered = discover_variables(tmpl.latex_source)
        config = auto_config_for_variables(discovered)
        existing = tmpl.variable_config or {}

        result = []
        for var in discovered:
            cfg = existing.get(var, config.get(var, {}))
            result.append({
                "name": var,
                "label": cfg.get("label", var),
                "type": cfg.get("type", "text"),
                "required": cfg.get("required", False),
            })
        serializer = DiscoveredVariableSerializer(result, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def preview(self, request, pk=None):
        tmpl = self.get_object()
        field_values = request.data.get("field_values", {})
        try:
            with tempfile.TemporaryDirectory(prefix="lettergen-preview-") as tmp:
                pdf = generate_pdf(tmpl.latex_source, field_values, Path(tmp))
                return FileResponse(
                    open(pdf, "rb"),
                    content_type="application/pdf",
                    filename="preview.pdf",
                )
        except LatexCompileError as e:
            detail = f"LaTeX error: {e}"
            if e.log:
                detail += f"\n\nLog:\n{e.log}"
            return Response({"detail": detail}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class CorrespondentProfileViewSet(viewsets.ModelViewSet):
    queryset = CorrespondentProfile.objects.select_related("paperless").all()
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return CorrespondentProfileWriteSerializer
        return CorrespondentProfileSerializer

    @action(detail=False, methods=["get"], url_path="by-paperless/(?P<paperless_id>[^/.]+)")
    def by_paperless(self, request, paperless_id=None):
        try:
            profile = CorrespondentProfile.objects.select_related("paperless").get(
                paperless_id=paperless_id,
            )
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except CorrespondentProfile.DoesNotExist:
            raise Http404


class LetterViewSet(viewsets.ModelViewSet):
    queryset = Letter.objects.select_related(
        "template", "correspondent_profile", "correspondent",
    ).all()
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return LetterWriteSerializer
        return LetterSerializer

    @action(detail=True, methods=["post"])
    def generate(self, request, pk=None):
        letter = self.get_object()
        if letter.status == Letter.Status.GENERATED:
            return Response(
                {"detail": _("Letter already generated")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        pdf_path = tasks.generate_letter_pdf(letter.pk)
        if pdf_path is None:
            return Response(
                {"detail": _("PDF generation failed")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        letter.refresh_from_db()
        serializer = self.get_serializer(letter)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        letter = self.get_object()
        if letter.status != Letter.Status.GENERATED:
            return Response(
                {"detail": _("Letter must be generated first")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ser = SendToPaperlessSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        doc_id = tasks.send_letter_to_paperless(
            letter.pk,
            title=ser.validated_data.get("title", ""),
            tag_ids=ser.validated_data.get("tags"),
        )
        if doc_id is None:
            return Response(
                {"detail": _("Failed to send to Paperless")},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        letter.refresh_from_db()
        serializer = self.get_serializer(letter)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def pdf(self, request, pk=None):
        letter = self.get_object()
        if not letter.pdf:
            raise Http404(_("No PDF available"))
        response = FileResponse(letter.pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="letter-{letter.pk}.pdf"'
        return response
