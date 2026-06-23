from django.urls import path, include
from rest_framework.routers import DefaultRouter

from paperless_lettergen.views import (
    LaTeXTemplateViewSet,
    CorrespondentProfileViewSet,
    LetterViewSet,
)

router = DefaultRouter()
router.register(r"lettergen_templates", LaTeXTemplateViewSet, basename="lettergen_template")
router.register(r"lettergen_profiles", CorrespondentProfileViewSet, basename="lettergen_profile")
router.register(r"lettergen_letters", LetterViewSet, basename="lettergen_letter")

urlpatterns = [
    path("", include(router.urls)),
]
