"""
Endpoints do perfil público do MC (nome completo, localização, biografia, foto).

Leitura pública (consumida pelo modal "Sobre o MC" no site do cliente);
escrita restrita ao painel admin via Bearer Token.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password, verify_admin_token, verify_password
from app.config import settings
from app.database import get_db
from app.models import MCProfile
from app.schemas.profile import AdminPasswordChange, MCProfileRead, MCProfileUpdate

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


@router.patch(
    "/admin-password",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_admin_token)],
)
async def change_admin_password(
    payload: AdminPasswordChange, db: AsyncSession = Depends(get_db)
) -> None:
    """
    [Admin] Permite ao próprio MC escolher a sua palavra-passe do painel
    admin, em vez de depender do ADMIN_TOKEN fixo definido no Render.
    """
    profile = await _get_or_create_profile(db)

    # Confirma a palavra-passe atual antes de trocar — mesma lógica de
    # verify_admin_token, para não depender só do Bearer Token já validado.
    current_ok = False
    if profile.admin_password_hash:
        current_ok = verify_password(payload.current_password, profile.admin_password_hash)
    else:
        current_ok = payload.current_password == settings.admin_token

    if not current_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Palavra-passe atual incorreta.",
        )

    profile.admin_password_hash = hash_password(payload.new_password)
    await db.commit()
