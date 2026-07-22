"""{{project_name}} web API application."""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="{{project_name}}")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
