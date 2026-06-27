import asyncio
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("paperless-letter-generator.paperless")


class PaperlessClient:
    def __init__(self):
        self.base_url = settings.paperless_api_url.rstrip("/")
        self.token = settings.paperless_api_token
        self._client: httpx.AsyncClient | None = None

    @property
    def headers(self) -> dict[str, str]:
        h = {"Accept": "application/json; version=6"}
        if self.token:
            h["Authorization"] = f"Token {self.token}"
        return h

    async def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=30)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def check_connection(self) -> bool:
        try:
            c = await self.client()
            r = await c.get("/api/correspondents/", params={"page_size": 1})
            return r.status_code == 200
        except Exception:
            return False

    async def list_correspondents(self) -> list[dict[str, Any]]:
        c = await self.client()
        results: list[dict[str, Any]] = []
        page = 1
        while True:
            r = await c.get("/api/correspondents/", params={"page": page, "page_size": 100})
            r.raise_for_status()
            data = r.json()
            results.extend(data.get("results", []))
            if data.get("next"):
                page += 1
            else:
                break
        return results

    async def get_document(self, doc_id: int) -> dict[str, Any] | None:
        c = await self.client()
        r = await c.get(f"/api/documents/{doc_id}/")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def search_documents(self, query: str, page_size: int = 20) -> list[dict[str, Any]]:
        c = await self.client()
        seen: set[int] = set()
        results: list[dict[str, Any]] = []
        for param in ("query", "title__icontains"):
            r = await c.get("/api/documents/", params={param: query, "page_size": page_size})
            r.raise_for_status()
            for doc in r.json().get("results", []):
                if doc["id"] not in seen:
                    seen.add(doc["id"])
                    results.append(doc)
        return results[:page_size]

    async def download_document_pdf(self, doc_id: int) -> bytes:
        c = await self.client()
        r = await c.get(f"/api/documents/{doc_id}/download/")
        r.raise_for_status()
        return r.content

    async def get_correspondent(self, corr_id: int) -> dict[str, Any] | None:
        c = await self.client()
        r = await c.get(f"/api/correspondents/{corr_id}/")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def _get_task_doc_id(self, task_uuid: str, max_retries: int = 30, delay: float = 1.0) -> int:
        """Poll /api/tasks/ until the task completes, return the document ID."""
        c = await self.client()
        for attempt in range(max_retries):
            try:
                r = await c.get("/api/tasks/")
                r.raise_for_status()
                tasks = r.json()
                for task in tasks:
                    if task.get("task_id") == task_uuid:
                        status = task.get("status", "")
                        if status == "SUCCESS":
                            doc_id = task.get("related_document")
                            if doc_id is not None:
                                return int(doc_id)
                            result_str = task.get("result", "")
                            import re
                            m = re.search(r"document id (\d+)", result_str, re.IGNORECASE)
                            if m:
                                return int(m.group(1))
                            raise RuntimeError(f"Task succeeded but no document ID found: {result_str}")
                        elif status == "FAILURE":
                            raise RuntimeError(f"Task failed: {task.get('result', 'unknown error')}")
                        break
            except httpx.HTTPError as e:
                logger.warning("Task poll attempt %d failed: %s", attempt + 1, e)
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
        raise TimeoutError(f"Task {task_uuid} did not complete within {max_retries * delay}s")

    async def post_document(
        self,
        pdf_path: str,
        title: str,
        correspondent_id: int | None = None,
        document_type_id: int | None = None,
        tags: list[int] | None = None,
    ) -> int:
        c = await self.client()
        with open(pdf_path, "rb") as f:
            files = {"document": (f"{title}.pdf", f, "application/pdf")}
            data: dict[str, Any] = {"title": title}
            if correspondent_id:
                data["correspondent"] = str(correspondent_id)
            if document_type_id:
                data["document_type"] = str(document_type_id)
            if tags:
                data["tags"] = [str(t) for t in tags]
            r = await c.post("/api/documents/post_document/", data=data, files=files)
            r.raise_for_status()
            logger.info("Paperless upload response status=%d", r.status_code)
            result = r.json()
            logger.info("Paperless upload response: %s", str(result)[:300])
            if isinstance(result, dict):
                task_uuid = result.get("task_id") or result.get("id") or result.get("task") or result.get("task_uuid") or ""
            elif isinstance(result, str):
                task_uuid = result
            else:
                task_uuid = ""
            if not task_uuid:
                raise RuntimeError(f"No task_id returned from Paperless upload. Response: {str(result)[:200]}")
            logger.info("Document upload queued, task_id=%s, waiting for completion...", task_uuid)
            doc_id = await self._get_task_doc_id(task_uuid)
            logger.info("Task completed, document id=%d", doc_id)
            return doc_id


paperless_client = PaperlessClient()
