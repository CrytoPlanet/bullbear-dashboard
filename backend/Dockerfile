FROM python:3.12-slim

WORKDIR /app

# Install Poetry directly (simpler for Docker)
RUN pip install --no-cache-dir -U pip poetry

# Copy dependency files and install
COPY pyproject.toml ./
RUN poetry lock --no-interaction && poetry install --only main --no-interaction --no-ansi --no-root

# Copy application code
COPY bullbear_backend ./bullbear_backend

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "bullbear_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
