"""
Endpoints para submissão de pedidos de orçamento (leads) e geração
do link de contacto pré-formatado via WhatsApp.
"""
import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_admin_token
from app.database import get_db
from app.models import BookingLead, LeadStatus, MCProfile, Package
from app.schemas.lead import (
    BookingLeadCreate,
    BookingLeadRead,
    BookingLeadStatusUpdate,
    WhatsAppLinkResponse,
)

router = APIRouter(prefix="/leads", tags=["Leads"])


def _to_read_model(lead: BookingLead) -> BookingLeadRead:
    """Converte o ORM para o schema de leitura, incluindo o nome do pacote."""
    data = BookingLeadRead.model_validate(lead)
    data.package_name = lead.package.name if lead.package else None
    return data


@router.post("", response_model=BookingLeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: BookingLeadCreate, db: AsyncSession = Depends(get_db)
) -> BookingLeadRead:
    """Recebe um pedido de orçamento/reserva do site e grava na base de dados."""
    if payload.selected_package_id is not None:
        package = await db.get(Package, payload.selected_package_id)
        if package is None or not package.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pacote selecionado inválido ou indisponível.",
            )

    lead = BookingLead(**payload.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return _to_read_model(lead)


@router.get(
    "",
    response_model=list[BookingLeadRead],
    dependencies=[Depends(verify_admin_token)],
)
async def list_leads(
    status_filter: LeadStatus | None = Query(
        default=None,
        alias="status",
        description="Filtra por estado: pending, contacted ou closed.",
    ),
    db: AsyncSession = Depends(get_db),
) -> list[BookingLeadRead]:
    """
    [Admin] Lista todos os pedidos de orçamento, do mais recente para o mais antigo.
    Usado pelo painel administrativo (admin.html) com filtros rápidos de estado.
    """
    query = select(BookingLead).order_by(BookingLead.created_at.desc())
    if status_filter is not None:
        query = query.where(BookingLead.status == status_filter)

    result = await db.execute(query)
    leads = result.scalars().all()
    return [_to_read_model(lead) for lead in leads]


@router.patch(
    "/{lead_id}",
    response_model=BookingLeadRead,
    dependencies=[Depends(verify_admin_token)],
)
async def update_lead_status(
    lead_id: uuid.UUID,
    payload: BookingLeadStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> BookingLeadRead:
    """[Admin] Atualiza o estado de um lead (pending / contacted / closed)."""
    lead = await db.get(BookingLead, lead_id)
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead não encontrado."
        )

    lead.status = payload.status
    await db.commit()
    await db.refresh(lead)
    return _to_read_model(lead)


@router.get("/whatsapp-link/{lead_id}", response_model=WhatsAppLinkResponse)
async def get_whatsapp_link(
    lead_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> WhatsAppLinkResponse:
    """
    Gera um link wa.me pré-formatado com o resumo do pedido (pacote, data,
    tipo de evento e preço estimado), pronto para o MC contactar o cliente.
    """
    result = await db.execute(
        select(BookingLead).where(BookingLead.id == lead_id)
    )
    lead = result.scalar_one_or_none()
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Lead não encontrado."
        )

    package_name = lead.package.name if lead.package else "Pacote personalizado"

    # Número de WhatsApp lido do perfil (editável no painel admin, não requer
    # alterar variáveis de ambiente no Render).
    profile = await db.get(MCProfile, 1)
    whatsapp_number = profile.whatsapp_number if profile else "258876050602"

    # Mensagem escrita da perspetiva do CLIENTE, dirigida ao MC — é o cliente
    # quem envia isto pelo WhatsApp, depois de simular o orçamento no site.
    message = (
        f"Olá! Sou {lead.client_name} 👋\n\n"
        f"Estive a ver o seu site e fiquei muito interessado(a) em contratar "
        f"os seus serviços para o meu evento. Aqui está o resumo do que "
        f"simulei:\n\n"
        f"🎉 Evento: {lead.event_type}\n"
        f"📅 Data: {lead.event_date.strftime('%d/%m/%Y')}\n"
        f"📦 Pacote: {package_name}\n"
        f"💰 Valor estimado: {lead.estimated_price:.2f} MT\n\n"
        f"Podemos conversar sobre os próximos passos e confirmar a "
        f"disponibilidade para esta data?"
    )

    encoded_message = quote(message)
    whatsapp_link = f"https://wa.me/{whatsapp_number}?text={encoded_message}"

    return WhatsAppLinkResponse(
        lead_id=lead.id,
        whatsapp_link=whatsapp_link,
        message_preview=message,
    )
