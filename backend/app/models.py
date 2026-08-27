"""
Modelos ORM (SQLAlchemy 2.0 typed style) para o sistema de portfólio e reservas do MC.
"""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy import Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

# Tipos de evento suportados no site — mantido em sincronia com o <select> do formulário
# em frontend/index.html. "Outro" cobre qualquer evento fora desta lista.
EVENT_TYPES: list[str] = [
    "Aniversário",
    "Casamento",
    "Corporativo",
    "Graduação",
    "Xitique",
    "Outro",
]


class MediaType(str, enum.Enum):
    VIDEO = "video"
    IMAGE = "image"


class LeadStatus(str, enum.Enum):
    PENDING = "pending"
    CONTACTED = "contacted"
    CLOSED = "closed"


class Package(Base):
    """Pacote de serviço oferecido pelo MC (ex: 'Casamento Clássico', 'Gala Corporativa')."""

    __tablename__ = "packages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    base_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    features: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    leads: Mapped[list["BookingLead"]] = relationship(
        back_populates="package", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Package {self.name} ({self.base_price})>"


class Media(Base):
    """Item de galeria (vídeo ou imagem) exibido no portfólio."""

    __tablename__ = "media"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    type: Mapped[MediaType] = mapped_column(
        Enum(MediaType, name="media_type_enum", native_enum=False), nullable=False
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Media {self.title} ({self.type})>"


class BookingLead(Base):
    """Pedido de orçamento/reserva submetido por um potencial cliente."""

    __tablename__ = "booking_leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_name: Mapped[str] = mapped_column(String(150), nullable=False)
    client_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)

    selected_package_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("packages.id", ondelete="SET NULL"), nullable=True
    )
    estimated_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="lead_status_enum", native_enum=False),
        default=LeadStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    package: Mapped["Package | None"] = relationship(
        back_populates="leads", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<BookingLead {self.client_name} - {self.event_date} ({self.status})>"


class BlockedDate(Base):
    """Data em que o MC já não está disponível (agenda ocupada/bloqueada manualmente)."""

    __tablename__ = "blocked_dates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<BlockedDate {self.date}>"


class MCProfile(Base):
    """
    Perfil público do Mestre de Cerimónias (linha única — este site representa
    um único MC, não é uma plataforma multi-utilizador).
    """

    __tablename__ = "mc_profile"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False, default="Alito Mucavel")
    location: Mapped[str] = mapped_column(String(150), nullable=False, default="Moçambique")
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    whatsapp_number: Mapped[str] = mapped_column(
        String(20), nullable=False, default="258876050602"
    )
    # Palavra-passe personalizada do painel admin, escolhida pelo próprio MC
    # (guardada como hash, nunca em texto simples). Se for None, o sistema
    # usa o ADMIN_TOKEN do .env/Render como valor de recurso (compatibilidade
    # com o que já estava configurado antes desta funcionalidade existir).
    admin_password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<MCProfile {self.full_name}>"


class EventCategoryInfo(Base):
    """
    Pequena descrição/motivação por tipo de evento, mostrada no site antes
    dos pacotes desse evento (ex: "O seu casamento vai ser..."). Editável
    no painel admin, sem precisar de tocar em código.
    """

    __tablename__ = "event_category_info"

    event_type: Mapped[str] = mapped_column(String(50), primary_key=True)
    tagline: Mapped[str] = mapped_column(Text, nullable=False, default="")

    def __repr__(self) -> str:
        return f"<EventCategoryInfo {self.event_type}>"


class Review(Base):
    """
    Avaliação/testemunho deixado por um cliente final do MC (não pelo MC),
    depois do evento. Exibido publicamente no site (quando aprovado), e
    listado no painel admin para o Alito perceber onde pode melhorar.
    """

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_name: Mapped[str] = mapped_column(String(150), nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rating: Mapped[int] = mapped_column(nullable=False)  # 1 a 5 estrelas
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    # Só avaliações aprovadas aparecem no site público — dá ao Alito controlo
    # editorial (ex: esconder um comentário injusto ou ofensivo) sem apagar
    # o registo, que continua visível no painel admin.
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return f"<Review {self.client_name} ({self.rating}★)>"
