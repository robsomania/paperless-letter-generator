from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PaperlessLettergenConfig(AppConfig):
    name = "paperless_lettergen"
    verbose_name = _("Paperless letter generator")

    def ready(self):
        from . import signals  # noqa: F401
