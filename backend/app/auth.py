"""
Autenticação simples para o painel administrativo do MC.

Usa um Bearer Token único (não é multi-utilizador nem OAuth) — adequado
para um único MC a gerir o próprio negócio a partir do telemóvel.

Duas fontes possíveis de credencial, nesta ordem de prioridade:
1. Palavra-passe personalizada, escolhida pelo próprio MC no painel admin
   (guardada como hash em mc_profile.admin_password_hash).
2. ADMIN_TOKEN definido no .env/Render — usado enquanto o MC ainda não
   escolheu a sua própria palavra-passe (valor de recurso/compatibilidade).
"""
import hashlib
import hmac
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import MCProfile

bearer_scheme = HTTPBearer(auto_error=False)

_PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    """Gera um hash seguro (salt aleatório + PBKDF2-HMAC-SHA256) para guardar na BD."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Confirma se `password` corresponde ao hash guardado, em tempo constante."""
    try:
        salt_hex, digest_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, AttributeError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return hmac.compare_digest(actual, expected)


async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Valida a credencial nas rotas /admin/*. Lança 401 se ausente ou inválida."""
    if not settings.admin_auth_enabled:
        # Autenticação desligada via ADMIN_AUTH_ENABLED=false no .env — só para testes.
        # LEMBRETE: voltar a ligar (ADMIN_AUTH_ENABLED=true) antes de publicar o site.
        return

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Palavra-passe de administrador em falta.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    supplied = credentials.credentials
    profile = await db.get(MCProfile, 1)

    if profile is not None and profile.admin_password_hash:
        # O MC já escolheu a sua própria palavra-passe — usar essa.
        if verify_password(supplied, profile.admin_password_hash):
            return
    else:
        # Ainda não foi definida nenhuma palavra-passe personalizada —
        # aceitar o ADMIN_TOKEN do .env/Render, como antes.
        if hmac.compare_digest(supplied, settings.admin_token):
            return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Palavra-passe de administrador inválida.",
        headers={"WWW-Authenticate": "Bearer"},
    )
