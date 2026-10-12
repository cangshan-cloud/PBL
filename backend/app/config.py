from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


def parse_cors_origins(value: str) -> tuple[str, ...]:
    origins = tuple(item.strip() for item in value.split(",") if item.strip())
    if not origins:
        raise ValueError("CORS_ORIGINS must contain at least one origin")
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
            or "*" in origin
        ):
            raise ValueError(f"CORS_ORIGINS contains an invalid origin: {origin}")
    return origins


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    task_execution_mode: str
    data_root: Path
    max_upload_bytes: int
    jwt_secret: str
    access_token_minutes: int
    bootstrap_admin_password: str
    bootstrap_researcher_password: str
    bootstrap_viewer_password: str
    cors_origins: tuple[str, ...]


def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./factorlab.db"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        task_execution_mode=os.getenv("TASK_EXECUTION_MODE", "inline"),
        data_root=Path(
            os.getenv("DATA_ROOT", str(Path(__file__).resolve().parents[2] / "data" / "runtime"))
        ),
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))),
        jwt_secret=os.getenv("JWT_SECRET", "development-only-change-me"),
        access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "120")),
        bootstrap_admin_password=os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "admin12345"),
        bootstrap_researcher_password=os.getenv("BOOTSTRAP_RESEARCHER_PASSWORD", "research12345"),
        bootstrap_viewer_password=os.getenv("BOOTSTRAP_VIEWER_PASSWORD", "viewer12345"),
        cors_origins=parse_cors_origins(os.getenv("CORS_ORIGINS", "http://localhost:5173")),
    )
