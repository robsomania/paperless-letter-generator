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
            try:
                r = await c.get("/api/documents/", params={param: query, "page_size": page_size})
                r.raise_for_status()
                for doc in r.json().get("results", []):
                    if doc["id"] not in seen:
                        seen.add(doc["id"])
                        results.append(doc)
            except Exception as e:
                logger.warning("Search with param '%s' failed: %s", param, e)
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
            r = await c.get("/api/tasks/")
            r.raise_for_status()
            tasks = r.json()
            for task in tasks:
                if task.get("task_id") == task_uuid:
                    status = task.get("status", "").upper()
                    if status == "SUCCESS":
                        doc_id = task.get("related_document")
                        if doc_id:
                            return doc_id
                        result = task.get("result") or ""
                        m = __import__("re").search(r"(\d+)", str(result))
                        if m:
                            return int(m.group(1))
                        raise RuntimeError(f"Task succeeded but no document ID found: {result}")
                    if status in ("FAILURE", "REVOKED"):
                        raise RuntimeError(f"Task failed: {task.get('result', 'unknown error')}")
            await asyncio.sleep(delay)
        raise TimeoutError(f"Task {task_uuid} did not complete within {max_retries * delay}s")

    async def post_document(self, pdf_path: str, title: str,
                            correspondent_id: int | None = None) -> int:
        c = await self.client()
        with open(pdf_path, "rb") as f:
            files = {"document": (f"{title}.pdf", f, "application/pdf")}
            data = {"title": title}
            if correspondent_id:
                data["correspondent"] = str(correspondent_id)
            r = await c.post("/api/documents/post_document/", data=data, files=files)
            r.raise_for_status()
        task_uuid = r.json().get("task_id")
        if not task_uuid:
            raise RuntimeError("No task_id returned from post_document")
        return await self._get_task_doc_id(str(task_uuid))


paperless_client = PaperlessClient()
