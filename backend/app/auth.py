"""
Autenticação simples para o painel administrativo do MC.

Usa um Bearer Token único (não é multi-utilizador nem OAuth) — adequado
para um único MC a gerir o próprio negócio a partir do telemóvel.
Definir o token real em ADMIN_TOKEN no .env.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    """Valida o Bearer Token nas rotas /admin/*. Lança 401 se ausente ou inválido."""
    if not settings.admin_auth_enabled:
        # Autenticação desligada via ADMIN_AUTH_ENABLED=false no .env — só para testes.
        # LEMBRETE: voltar a ligar (ADMIN_AUTH_ENABLED=true) antes de publicar o site.
        return

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de administrador em falta.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de administrador inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
