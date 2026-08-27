"""Schemas Pydantic v2 para o recurso MCProfile."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MCProfileRead(BaseModel):
    full_name: str
    location: str
    bio: str
    photo_url: str | None
    whatsapp_number: str
    payment_terms: str | None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MCProfileUpdate(BaseModel):
    """Payload para atualização — usado pelo painel admin (rota protegida)."""

    full_name: str | None = Field(default=None, max_length=150)
    location: str | None = Field(default=None, max_length=150)
    bio: str | None = None
    photo_url: str | None = Field(default=None, max_length=500)
    whatsapp_number: str | None = Field(default=None, max_length=20)
    payment_terms: str | None = None

    @field_validator("whatsapp_number")
    @classmethod
    def clean_whatsapp(cls, v: str | None) -> str | None:
        if v is None:
            return v
        cleaned = "".join(ch for ch in v if ch.isdigit())
        if len(cleaned) < 9:
            raise ValueError("Número de WhatsApp inválido.")
        return cleaned


class AdminPasswordChange(BaseModel):
    """Payload para o MC escolher a sua própria palavra-passe do painel admin."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=100)
