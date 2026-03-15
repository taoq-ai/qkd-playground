"""FastAPI application factory."""

from fastapi import FastAPI

from qkd_playground.domain.models import ProtocolType


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="QKD Playground",
        description="Quantum Key Distribution simulator API",
        version="0.1.0",
    )

    @app.get("/protocols")
    async def list_protocols() -> list[dict[str, str]]:
        return [{"name": p.value, "label": p.name} for p in ProtocolType]

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
