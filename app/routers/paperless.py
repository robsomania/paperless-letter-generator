import logging

from fastapi import APIRouter, HTTPException

from app.schemas import PaperlessCorrespondent, PaperlessDocument
from app.services.paperless_client import paperless_client

logger = logging.getLogger("paperless-letter-generator.paperless")
router = APIRouter(prefix="/api/paperless", tags=["paperless"])


@router.get("/me")
async def check_connection():
    ok = await paperless_client.check_connection()
    if not ok:
        raise HTTPException(502, "Cannot connect to Paperless-ngx API")
    return {"status": "ok", "url": paperless_client.base_url}


@router.get("/correspondents", response_model=list[PaperlessCorrespondent])
async def list_correspondents():
    try:
        data = await paperless_client.list_correspondents()
        result: list[PaperlessCorrespondent] = []
        for c in data:
            result.append(PaperlessCorrespondent(
                id=c["id"],
                name=c.get("name", ""),
                last_correspondence=c.get("last_correspondence"),
                document_count=c.get("document_count"),
            ))
        return result
    except Exception as e:
        raise HTTPException(502, f"Failed to fetch correspondents: {e}")


@router.get("/documents/search")
async def search_documents(q: str = ""):
    if not q.strip():
        return []
    try:
        data = await paperless_client.search_documents(q.strip())
        result: list[dict] = []
        for d in data:
            result.append({
                "id": d["id"],
                "title": d.get("title", ""),
                "correspondent_name": d.get("correspondent_name"),
                "created": d.get("created"),
            })
        return result
    except Exception as e:
        raise HTTPException(502, f"Failed to search documents: {e}")


@router.get("/documents/{document_id}", response_model=PaperlessDocument)
async def get_document(document_id: int):
    try:
        data = await paperless_client.get_document(document_id)
        if not data:
            raise HTTPException(404, "Document not found in Paperless")
        return PaperlessDocument(
            id=data["id"],
            title=data.get("title", ""),
            correspondent=data.get("correspondent"),
            correspondent_name=data.get("correspondent_name"),
            created=data.get("created"),
            added=data.get("added"),
            tags=data.get("tags", []),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Failed to fetch document: {e}")


@router.get("/correspondents/{correspondent_id}")
async def get_correspondent(correspondent_id: int):
    try:
        data = await paperless_client.get_correspondent(correspondent_id)
        if not data:
            raise HTTPException(404, "Correspondent not found in Paperless")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"Failed to fetch correspondent: {e}")
