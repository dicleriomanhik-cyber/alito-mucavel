"""
Endpoints de avaliações/testemunhos deixados pelos clientes finais do MC.

Submissão pública (qualquer cliente pode deixar a sua avaliação depois do
evento); leitura pública só mostra avaliações aprovadas (para o site);
moderação e leitura completa restritas ao painel admin via Bearer Token.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_admin_token
from app.database import get_db
from app.models import Review
from app.schemas.review import ReviewCreate, ReviewModerate, ReviewRead

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("", response_model=list[ReviewRead])
async def list_reviews(
    include_unpublished: bool = False, db: AsyncSession = Depends(get_db)
) -> list[Review]:
    """
    Lista avaliações, da mais recente para a mais antiga.
    Por omissão só as aprovadas (usado pelo site público);
    `include_unpublished=true` devolve tudo (usado pelo painel admin).
    """
    query = select(Review).order_by(Review.created_at.desc())
    if not include_unpublished:
        query = query.where(Review.is_published.is_(True))

    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(payload: ReviewCreate, db: AsyncSession = Depends(get_db)) -> Review:
    """Recebe uma avaliação submetida por um cliente final do MC, no site público."""
    review = Review(**payload.model_dump())
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@router.patch(
    "/{review_id}",
    response_model=ReviewRead,
    dependencies=[Depends(verify_admin_token)],
)
async def moderate_review(
    review_id: uuid.UUID, payload: ReviewModerate, db: AsyncSession = Depends(get_db)
) -> Review:
    """[Admin] Aprova ou esconde uma avaliação do site público, sem a apagar."""
    review = await db.get(Review, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Avaliação não encontrada."
        )
    review.is_published = payload.is_published
    await db.commit()
    await db.refresh(review)
    return review


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_admin_token)],
)
async def delete_review(review_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    """[Admin] Remove uma avaliação permanentemente."""
    review = await db.get(Review, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Avaliação não encontrada."
        )
    await db.delete(review)
    await db.commit()
