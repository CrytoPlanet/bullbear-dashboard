from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="BullBear Backend", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"ok": True, "service": "bullbear-backend"}


