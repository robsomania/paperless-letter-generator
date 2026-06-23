from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    paperless_api_url: str = "http://localhost:8000"
    paperless_api_token: str = ""

    listen_host: str = "0.0.0.0"
    listen_port: int = 8050

    database_url: str = "sqlite:///data/paperless-letter-generator.db"
    data_dir: str = "data"

    log_level: str = "info"

    @property
    def data_path(self) -> Path:
        return Path(self.data_dir).resolve()

    @property
    def pdfs_path(self) -> Path:
        return self.data_path / "pdfs"

    @property
    def db_path(self) -> Path:
        if self.database_url.startswith("sqlite:///"):
            rel = self.database_url[len("sqlite:///"):]
            return Path(rel).resolve()
        return Path(self.data_dir).resolve() / "paperless-letter-generator.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
