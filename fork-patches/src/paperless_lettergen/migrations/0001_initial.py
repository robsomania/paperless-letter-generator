from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("documents", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LaTeXTemplate",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, verbose_name="name")),
                ("description", models.TextField(blank=True, default="", verbose_name="description")),
                ("latex_source", models.TextField(verbose_name="LaTeX source")),
                ("variable_config", models.JSONField(blank=True, default=dict, verbose_name="variable configuration")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="updated at")),
            ],
            options={
                "verbose_name": "LaTeX template",
                "verbose_name_plural": "LaTeX templates",
                "ordering": ("-updated_at",),
            },
        ),
        migrations.CreateModel(
            name="CorrespondentProfile",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("salutation", models.CharField(blank=True, default="", max_length=50, verbose_name="salutation")),
                ("company", models.CharField(blank=True, default="", max_length=255, verbose_name="company")),
                ("street", models.CharField(blank=True, default="", max_length=255, verbose_name="street")),
                ("zip_city", models.CharField(blank=True, default="", max_length=255, verbose_name="ZIP / city")),
                ("country", models.CharField(blank=True, default="", max_length=255, verbose_name="country")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="updated at")),
                (
                    "paperless",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lettergen_profile",
                        to="documents.correspondent",
                        verbose_name="correspondent",
                    ),
                ),
            ],
            options={
                "verbose_name": "correspondent profile",
                "verbose_name_plural": "correspondent profiles",
            },
        ),
        migrations.CreateModel(
            name="Letter",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("field_values", models.JSONField(blank=True, default=dict, verbose_name="field values")),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("generated", "Generated"), ("sent", "Sent")],
                        default="draft",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                ("pdf", models.FileField(blank=True, null=True, upload_to="lettergen/", verbose_name="PDF")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="updated at")),
                (
                    "correspondent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="documents.correspondent",
                        verbose_name="correspondent",
                    ),
                ),
                (
                    "correspondent_profile",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="paperless_lettergen.correspondentprofile",
                        verbose_name="correspondent profile",
                    ),
                ),
                (
                    "result_document",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="documents.document",
                        verbose_name="result document",
                    ),
                ),
                (
                    "source_document",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="documents.document",
                        verbose_name="source document",
                    ),
                ),
                (
                    "template",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="letters",
                        to="paperless_lettergen.latextemplate",
                        verbose_name="template",
                    ),
                ),
            ],
            options={
                "verbose_name": "letter",
                "verbose_name_plural": "letters",
                "ordering": ("-created_at",),
            },
        ),
    ]
