FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN python -c 'import pathlib, tomllib; metadata = tomllib.loads(pathlib.Path("pyproject.toml").read_text()); pathlib.Path("/tmp/requirements.txt").write_text("\n".join(metadata["project"]["dependencies"]) + "\n")' \
    && pip install --no-cache-dir -r /tmp/requirements.txt
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
