## BullBear Backend (Python)

This folder contains a minimal Python backend skeleton for the **Crypto Market State Machine** ([Notion spec](https://www.notion.so/dunion/Crypto-Market-State-Machine-2d871b69c5b7809c8e9bdf8f317b6a0b)).

### What’s implemented (skeleton)

- FastAPI app with a single health endpoint: `GET /api/health`

---

### Local dev (Poetry)

Prereqs:
- Python 3.12+
- Poetry (recommended install via `uv`)

Install Poetry with uv (fast, isolated):

```bash
uv tool install poetry
```

Install deps and run:

```bash
cd backend
poetry install
poetry run uvicorn bullbear_backend.main:app --reload --host 0.0.0.0 --port 8000
```

---

### Docker (recommended for quick spin-up)

From `backend/`:

```bash
docker compose up --build
```

Then open:
- `http://localhost:8000/api/health`


