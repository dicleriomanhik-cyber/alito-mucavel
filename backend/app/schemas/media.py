"""Schemas Pydantic v2 para o recurso Media (galeria)."""
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models import MediaType


class MediaBase(BaseModel):
    title: str = Field(..., max_length=150)
    type: MediaType
    url: str = Field(..., max_length=500)
    thumbnail_url: str | None = Field(default=None, max_length=500)
    is_active: bool = True


class MediaCreate(MediaBase):
    """Payload para criação — usado pelo painel admin (rota protegida)."""
    pass


class MediaUpdate(BaseModel):
    """Payload para atualização parcial — usado pelo painel admin (rota protegida)."""

    title: str | None = Field(default=None, max_length=150)
    type: MediaType | None = None
    url: str | None = Field(default=None, max_length=500)
    thumbnail_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class MediaRead(MediaBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
