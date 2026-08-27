"""Schemas Pydantic v2 para o recurso Review (avaliações/testemunhos de clientes)."""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewCreate(BaseModel):
    """Payload público — preenchido pelo cliente final do MC, depois do evento."""

    client_name: str = Field(..., min_length=2, max_length=150)
    event_type: str | None = Field(default=None, max_length=100)
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=3, max_length=1000)

    @field_validator("client_name", "comment")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()


class ReviewRead(BaseModel):
    id: uuid.UUID
    client_name: str
    event_type: str | None
    rating: int
    comment: str
    is_published: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewModerate(BaseModel):
    """[Admin] Aprovar/esconder uma avaliação sem a apagar."""

    is_published: bool
