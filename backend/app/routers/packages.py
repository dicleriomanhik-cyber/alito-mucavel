"""
Endpoints de pacotes de serviço.

Leitura pública, filtrável por tipo de evento (o formulário do site pede
primeiro o tipo de evento, depois carrega só os pacotes correspondentes).
Escrita (criar/editar/remover) restrita ao painel admin via Bearer Token.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_admin_token
from app.database import get_db
from app.models import EVENT_TYPES, Package
from app.schemas.package import PackageCreate, PackageRead, PackageUpdate

router = APIRouter(prefix="/packages", tags=["Packages"])


@router.get("", response_model=list[PackageRead])
async def list_packages(
    event_type: str | None = Query(
        default=None, description=f"Filtra por tipo de evento: {', '.join(EVENT_TYPES)}"
    ),
    db: AsyncSession = Depends(get_db),
) -> list[Package]:
    """
    Lista pacotes ativos, ordenados por preço.
    Sem `event_type`, devolve todos (útil para o painel admin gerir tudo de uma vez).
    """
    query = select(Package).where(Package.is_active.is_(True)).order_by(Package.base_price)
    if event_type is not None:
        query = query.where(Package.event_type == event_type)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.post(
    "",
    response_model=PackageRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_admin_token)],
)
async def create_package(
    payload: PackageCreate, db: AsyncSession = Depends(get_db)
) -> Package:
    """[Admin] Cria um novo pacote associado a um tipo de evento."""
    package = Package(**payload.model_dump())
    db.add(package)
    await db.commit()
    await db.refresh(package)
    return package


@router.patch(
    "/{package_id}",
    response_model=PackageRead,
    dependencies=[Depends(verify_admin_token)],
)
async def update_package(
    package_id: uuid.UUID, payload: PackageUpdate, db: AsyncSession = Depends(get_db)
) -> Package:
    """[Admin] Atualiza um pacote existente (preço, descrição, ativo/inativo, etc.)."""
    package = await db.get(Package, package_id)
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pacote não encontrado."
        )

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(package, field, value)

    await db.commit()
    await db.refresh(package)
    return package


@router.delete(
    "/{package_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_admin_token)],
)
async def delete_package(package_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    """[Admin] Remove um pacote permanentemente."""
    package = await db.get(Package, package_id)
    if package is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pacote não encontrado."
        )
    await db.delete(package)
    await db.commit()
