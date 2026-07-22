"""{{project_name}} web API application."""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(title="{{project_name}}")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
