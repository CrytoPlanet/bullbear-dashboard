FROM python:3.12-slim

WORKDIR /app

# Keep minimal; install Poetry via uv (fast, isolated)
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir uv
RUN uv tool install poetry

COPY pyproject.toml ./
RUN poetry lock --no-interaction && poetry install --only main --no-interaction --no-ansi --no-root

COPY bullbear_backend ./bullbear_backend

EXPOSE 8000

CMD ["uvicorn", "bullbear_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]


