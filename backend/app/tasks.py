from __future__ import annotations

from celery import Celery

from app.config import get_settings
from app.db import SessionLocal
from app.services.runs import execute_research_run


settings = get_settings()
celery_app = Celery("factorlab", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    broker_connection_retry_on_startup=True,
)


@celery_app.task(name="factorlab.execute_research_run")
def execute_research_run_task(run_id: str) -> str:
    with SessionLocal() as session:
        execute_research_run(session, run_id)
    return run_id

