"""Schemas Pydantic v2 para o recurso EventCategoryInfo."""
from pydantic import BaseModel


class EventCategoryInfoRead(BaseModel):
    event_type: str
    tagline: str

    class Config:
        from_attributes = True


class EventCategoryInfoUpdate(BaseModel):
    tagline: str
