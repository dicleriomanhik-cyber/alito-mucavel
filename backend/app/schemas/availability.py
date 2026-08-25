"""Schemas Pydantic v2 para o recurso BlockedDate (agenda de indisponibilidade)."""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BlockedDateCreate(BaseModel):
    date: date
    reason: str | None = Field(default=None, max_length=200)


class BlockedDateRead(BaseModel):
    id: uuid.UUID
    date: date
    reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
