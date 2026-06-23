import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import templates, letters, correspondents, paperless, senders, variables
from app.services.paperless_client import paperless_client

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("paperless-letter-generator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.pdfs_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data directory: {settings.data_path}")
    logger.info(f"PDFs directory: {settings.pdfs_path}")
    yield
    await paperless_client.close()


app = FastAPI(
    title="Paperless Letter Generator",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(templates.router)
app.include_router(letters.router)
app.include_router(correspondents.router)
app.include_router(paperless.router)
app.include_router(senders.router)
app.include_router(variables.router)


static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    logger.info(f"Serving frontend from {static_dir}")
else:
    logger.warning("No static directory found; frontend not available")


@app.get("/api/health")
def health():
    return {"status": "ok"}
