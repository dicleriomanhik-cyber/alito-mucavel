"""
Endpoints de galeria (portfólio de fotos/vídeos).

Leitura pública (consumida pelo site do cliente); criação, edição e
remoção restritas ao painel admin via Bearer Token — para o Alito poder
adicionar fotos/vídeos sem precisar de mexer em código.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_admin_token
from app.database import get_db
from app.models import Media
from app.schemas.media import MediaCreate, MediaRead, MediaUpdate

router = APIRouter(prefix="/gallery", tags=["Gallery"])


@router.get("", response_model=list[MediaRead])
async def list_gallery(
    include_inactive: bool = False, db: AsyncSession = Depends(get_db)
) -> list[Media]:
    """
    Lista mídia da galeria. Por omissão só a ativa (usado pelo site público);
    `include_inactive=true` devolve tudo (usado pelo painel admin).
    """
    query = select(Media).order_by(Media.created_at.desc())
    if not include_inactive:
        query = query.where(Media.is_active.is_(True))

    result = await db.execute(query)
    return list(result.scalars().all())


@router.post(
    "",
    response_model=MediaRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_admin_token)],
)
async def create_media(payload: MediaCreate, db: AsyncSession = Depends(get_db)) -> Media:
    """[Admin] Adiciona uma foto/vídeo à galeria."""
    media = Media(**payload.model_dump())
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media


@router.patch(
    "/{media_id}",
    response_model=MediaRead,
    dependencies=[Depends(verify_admin_token)],
)
async def update_media(
    media_id: uuid.UUID, payload: MediaUpdate, db: AsyncSession = Depends(get_db)
) -> Media:
    """[Admin] Atualiza um item da galeria (título, link, ativo/inativo, etc.)."""
    media = await db.get(Media, media_id)
    if media is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item da galeria não encontrado."
        )

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(media, field, value)

    await db.commit()
    await db.refresh(media)
    return media


@router.delete(
    "/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_admin_token)],
)
async def delete_media(media_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    """[Admin] Remove um item da galeria permanentemente."""
    media = await db.get(Media, media_id)
    if media is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item da galeria não encontrado."
        )
    await db.delete(media)
    await db.commit()
