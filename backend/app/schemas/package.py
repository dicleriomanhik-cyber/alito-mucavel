"""Schemas Pydantic v2 para o recurso Package."""
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import EVENT_TYPES


class PackageBase(BaseModel):
    name: str = Field(..., max_length=150)
    event_type: str = Field(
        ..., description=f"Um de: {', '.join(EVENT_TYPES)}"
    )
    description: str
    base_price: Decimal = Field(..., ge=0)
    features: list[str] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in EVENT_TYPES:
            raise ValueError(f"event_type deve ser um de: {', '.join(EVENT_TYPES)}")
        return v


class PackageCreate(PackageBase):
    """Payload para criação — usado pelo painel admin (rota protegida)."""
    pass


class PackageUpdate(BaseModel):
    """Payload para atualização parcial — usado pelo painel admin (rota protegida)."""

    name: str | None = Field(default=None, max_length=150)
    event_type: str | None = None
    description: str | None = None
    base_price: Decimal | None = Field(default=None, ge=0)
    features: list[str] | None = None
    is_active: bool | None = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str | None) -> str | None:
        if v is not None and v not in EVENT_TYPES:
            raise ValueError(f"event_type deve ser um de: {', '.join(EVENT_TYPES)}")
        return v


class PackageRead(PackageBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
