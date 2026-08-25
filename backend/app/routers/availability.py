"""
Endpoints de disponibilidade de agenda.

Leitura é pública (o site/formulário pode desabilitar datas já bloqueadas
ao cliente); escrita é restrita ao painel admin via Bearer Token.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_admin_token
from app.database import get_db
from app.models import BlockedDate
from app.schemas.availability import BlockedDateCreate, BlockedDateRead

router = APIRouter(prefix="/availability", tags=["Availability"])


@router.get("", response_model=list[BlockedDateRead])
async def list_blocked_dates(db: AsyncSession = Depends(get_db)) -> list[BlockedDate]:
    """Lista todas as datas atualmente bloqueadas na agenda do MC."""
    result = await db.execute(select(BlockedDate).order_by(BlockedDate.date))
    return list(result.scalars().all())


@router.post(
    "",
    response_model=BlockedDateRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_admin_token)],
)
async def block_date(
    payload: BlockedDateCreate, db: AsyncSession = Depends(get_db)
) -> BlockedDate:
    """[Admin] Marca uma data como indisponível (ex: já reservada informalmente)."""
    blocked = BlockedDate(**payload.model_dump())
    db.add(blocked)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta data já está bloqueada.",
        ) from exc
    await db.refresh(blocked)
    return blocked


@router.delete(
    "/{blocked_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_admin_token)],
)
async def unblock_date(blocked_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    """[Admin] Remove o bloqueio de uma data, tornando-a disponível novamente."""
    blocked = await db.get(BlockedDate, blocked_id)
    if blocked is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Data bloqueada não encontrada."
        )
    await db.delete(blocked)
    await db.commit()
