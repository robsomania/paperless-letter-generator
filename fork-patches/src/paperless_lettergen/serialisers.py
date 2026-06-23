from rest_framework import serializers

from paperless_lettergen.models import LaTeXTemplate, CorrespondentProfile, Letter


class VariableConfigField(serializers.Field):
    def to_representation(self, value):
        return value or {}

    def to_internal_value(self, data):
        return data or {}


class LaTeXTemplateSerializer(serializers.ModelSerializer):
    variable_config = VariableConfigField()

    class Meta:
        model = LaTeXTemplate
        fields = [
            "id", "name", "description", "latex_source",
            "variable_config", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CorrespondentProfileSerializer(serializers.ModelSerializer):
    paperless_id = serializers.IntegerField(source="paperless_id", read_only=True)

    class Meta:
        model = CorrespondentProfile
        fields = [
            "id", "paperless", "paperless_id", "salutation", "company",
            "street", "zip_city", "country", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CorrespondentProfileWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CorrespondentProfile
        fields = [
            "id", "paperless", "salutation", "company",
            "street", "zip_city", "country",
        ]


class LetterSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source="template.name", read_only=True)
    correspondent_name = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Letter
        fields = [
            "id", "template", "template_name", "correspondent_profile",
            "correspondent", "correspondent_name",
            "source_document", "result_document",
            "field_values", "status", "pdf", "pdf_url",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "status", "pdf", "pdf_url",
            "result_document", "created_at", "updated_at",
        ]

    def get_correspondent_name(self, obj):
        if obj.correspondent:
            return obj.correspondent.name
        if obj.correspondent_profile:
            return obj.correspondent_profile.paperless.name
        return None

    def get_pdf_url(self, obj):
        if obj.pdf and obj.pdf.name:
            return obj.pdf.url
        return None


class LetterWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Letter
        fields = [
            "template", "correspondent_profile", "correspondent",
            "source_document", "field_values",
        ]


class DiscoveredVariableSerializer(serializers.Serializer):
    name = serializers.CharField()
    label = serializers.CharField()
    type = serializers.CharField()
    required = serializers.BooleanField()


class SendToPaperlessSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True, default="")
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )
