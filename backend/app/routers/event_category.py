"""
Endpoints da pequena descrição/motivação de cada tipo de evento
(mostrada no site antes dos pacotes desse evento).

Leitura pública; escrita restrita ao painel admin via Bearer Token.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_admin_token
from app.database import get_db
from app.models import EVENT_TYPES, EventCategoryInfo
from app.schemas.event_category import EventCategoryInfoRead, EventCategoryInfoUpdate

router = APIRouter(prefix="/event-info", tags=["Event Category Info"])


@router.get("", response_model=list[EventCategoryInfoRead])
async def list_event_info(db: AsyncSession = Depends(get_db)) -> list[EventCategoryInfo]:
    """
    Devolve a descrição de cada tipo de evento. Tipos ainda sem descrição
    guardada aparecem com tagline vazia (o site mostra só o nome do evento).
    """
    result = await db.execute(select(EventCategoryInfo))
    existing = {row.event_type: row for row in result.scalars().all()}

    return [
        existing.get(event_type) or EventCategoryInfo(event_type=event_type, tagline="")
        for event_type in EVENT_TYPES
    ]


@router.put(
    "/{event_type}",
    response_model=EventCategoryInfoRead,
    dependencies=[Depends(verify_admin_token)],
)
async def update_event_info(
    event_type: str, payload: EventCategoryInfoUpdate, db: AsyncSession = Depends(get_db)
) -> EventCategoryInfo:
    """[Admin] Atualiza (ou cria) a descrição de um tipo de evento."""
    if event_type not in EVENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"event_type deve ser um de: {', '.join(EVENT_TYPES)}",
        )

    info = await db.get(EventCategoryInfo, event_type)
    if info is None:
        info = EventCategoryInfo(event_type=event_type, tagline=payload.tagline)
        db.add(info)
    else:
        info.tagline = payload.tagline

    await db.commit()
    await db.refresh(info)
    return info
