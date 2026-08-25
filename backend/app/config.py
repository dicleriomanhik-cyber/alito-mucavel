"""
Configurações globais da aplicação, carregadas de variáveis de ambiente (.env).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Base de Dados ---
    # Exemplo Supabase:  postgresql+asyncpg://postgres:<password>@<host>:5432/postgres
    # Exemplo Neon:      postgresql+asyncpg://<user>:<password>@<host>/<db>?ssl=require
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/mc_booking"

    # --- WhatsApp ---
    # Nota: o número de WhatsApp usado nos links reais vem do perfil na base
    # de dados (editável no painel admin, secção "O seu perfil"), não daqui.
    # Este valor só serve de valor por omissão da primeira vez que o perfil é criado.
    whatsapp_number: str = "258876050602"

    # --- Painel Administrativo ---
    # Token simples usado no admin.html (Authorization: Bearer <admin_token>).
    # Gerar um valor forte em produção, ex: openssl rand -hex 32
    admin_token: str = "changeme-token"

    # Interruptor para desligar a autenticação do admin TEMPORARIAMENTE
    # (útil em fase de testes). Em produção, deixar sempre True.
    # Para desligar: ADMIN_AUTH_ENABLED=false no .env — não apagar código.
    admin_auth_enabled: bool = True

    # --- App ---
    app_name: str = "MC Booking API"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]  # Em produção, restringir ao domínio do site
    environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cache das settings para evitar reler o .env em cada request."""
    return Settings()


settings = get_settings()
