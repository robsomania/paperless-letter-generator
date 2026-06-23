from fastapi import APIRouter

from app.services.template_vars import get_known_variable_configs

router = APIRouter(prefix="/api/known-variables", tags=["variables"])


@router.get("")
def list_known_variables():
    return get_known_variable_configs()
