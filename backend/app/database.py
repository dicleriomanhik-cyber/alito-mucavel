"""
Configuração da engine assíncrona, sessão e Base declarativa do SQLAlchemy.
Compatível com Supabase e Neon (Postgres via asyncpg).
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    pool_pre_ping=True,  # evita erros de conexão "stale" em serviços serverless
    future=True,
    # Necessário quando a ligação passa pelo "Transaction Pooler" do Supabase
    # (porta 6543, PgBouncer) — sem isto, o asyncpg tenta reutilizar prepared
    # statements que o PgBouncer não suporta neste modo, e a ligação falha
    # com "prepared statement already exists". Ligação direta (porta 5432)
    # não é afetada por isto, mas manter esta opção não faz mal nesse caso.
    connect_args={"statement_cache_size": 0},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Classe base declarativa para todos os modelos ORM."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency do FastAPI: fornece uma sessão de BD por request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_models() -> None:
    """
    Cria as tabelas no arranque (útil em dev).
    Em produção, preferir Alembic para migrações versionadas.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Migração leve para colunas novas em tabelas que já existiam antes
        # desta coluna ser criada (create_all não altera tabelas existentes).
        # Idempotente — corre em todos os arranques sem problema.
        from sqlalchemy import text

        await conn.execute(
            text(
                "ALTER TABLE mc_profile "
                "ADD COLUMN IF NOT EXISTS admin_password_hash VARCHAR(255)"
            )
        )
