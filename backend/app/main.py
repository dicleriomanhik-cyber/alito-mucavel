"""
Ponto de entrada da API — Site Portfólio e Sistema de Reservas para MC de Eventos.

Executar localmente:
    uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_models
from app.routers import availability, event_category, gallery, leads, packages, profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Em produção real, substituir por migrações Alembic.
    if settings.environment == "development":
        await init_models()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="API para portfólio e reservas de um Mestre de Cerimónias.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(packages.router, prefix=settings.api_v1_prefix)
app.include_router(gallery.router, prefix=settings.api_v1_prefix)
app.include_router(leads.router, prefix=settings.api_v1_prefix)
app.include_router(availability.router, prefix=settings.api_v1_prefix)
app.include_router(profile.router, prefix=settings.api_v1_prefix)
app.include_router(event_category.router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Endpoint simples para verificação de disponibilidade (uptime checks)."""
    return {"status": "ok", "service": settings.app_name}
