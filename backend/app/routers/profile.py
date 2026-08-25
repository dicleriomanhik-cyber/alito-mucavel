"""
Endpoints do perfil público do MC (nome completo, localização, biografia, foto).

Leitura pública (consumida pelo modal "Sobre o MC" no site do cliente);
escrita restrita ao painel admin via Bearer Token.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_admin_token
from app.database import get_db
from app.models import MCProfile
from app.schemas.profile import MCProfileRead, MCProfileUpdate

router = APIRouter(prefix="/profile", tags=["Profile"])

_PROFILE_ID = 1  # linha única — este site representa um único MC


async def _get_or_create_profile(db: AsyncSession) -> MCProfile:
    """Devolve o perfil existente ou cria um com valores por omissão na primeira vez."""
    profile = await db.get(MCProfile, _PROFILE_ID)
    if profile is None:
        profile = MCProfile(id=_PROFILE_ID)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile


@router.get("", response_model=MCProfileRead)
async def get_profile(db: AsyncSession = Depends(get_db)) -> MCProfile:
    """Devolve o perfil público do MC (nome, localização, bio, foto)."""
    return await _get_or_create_profile(db)


@router.put(
    "",
    response_model=MCProfileRead,
    dependencies=[Depends(verify_admin_token)],
)
async def update_profile(
    payload: MCProfileUpdate, db: AsyncSession = Depends(get_db)
) -> MCProfile:
    """[Admin] Atualiza os dados do perfil (usado pelo painel admin.html)."""
    profile = await _get_or_create_profile(db)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile
