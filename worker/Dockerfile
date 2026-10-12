FROM python:3.12-slim
WORKDIR /app
COPY backend/pyproject.toml ./
RUN python -c 'import pathlib, tomllib; metadata = tomllib.loads(pathlib.Path("pyproject.toml").read_text()); pathlib.Path("/tmp/requirements.txt").write_text("\n".join(metadata["project"]["dependencies"]) + "\n")' \
    && pip install --no-cache-dir -r /tmp/requirements.txt
COPY backend/app ./app
CMD ["celery", "-A", "app.tasks:celery_app", "worker", "--loglevel=INFO", "--concurrency=1"]
