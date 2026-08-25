"""Schemas Pydantic v2 para o recurso BookingLead."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import LeadStatus


class BookingLeadCreate(BaseModel):
    """Payload recebido do formulário público de orçamento/reserva."""

    client_name: str = Field(..., min_length=2, max_length=150)
    client_phone: str = Field(..., min_length=8, max_length=30)
    event_date: date
    event_type: str = Field(..., max_length=100)
    selected_package_id: uuid.UUID | None = None
    estimated_price: Decimal = Field(..., ge=0)

    @field_validator("event_date")
    @classmethod
    def event_date_must_be_future(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("A data do evento não pode estar no passado.")
        return v

    @field_validator("client_phone")
    @classmethod
    def phone_digits_only(cls, v: str) -> str:
        cleaned = "".join(ch for ch in v if ch.isdigit() or ch == "+")
        if len(cleaned) < 8:
            raise ValueError("Número de telefone inválido.")
        return cleaned


class BookingLeadRead(BaseModel):
    id: uuid.UUID
    client_name: str
    client_phone: str
    event_date: date
    event_type: str
    selected_package_id: uuid.UUID | None
    package_name: str | None = None
    estimated_price: Decimal
    status: LeadStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookingLeadStatusUpdate(BaseModel):
    """Payload do painel admin para atualizar o estado de um lead."""

    status: LeadStatus


class WhatsAppLinkResponse(BaseModel):
    """Resposta contendo o link pré-formatado para contacto via WhatsApp."""

    lead_id: uuid.UUID
    whatsapp_link: str
    message_preview: str
