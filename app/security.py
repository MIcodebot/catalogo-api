"""Hash de senha (PBKDF2, só biblioteca padrão) e tokens JWT."""

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings

ALGORITHM = "HS256"
_ITERACOES = 600_000


def gerar_hash(senha: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, _ITERACOES)
    partes = [
        "pbkdf2_sha256",
        str(_ITERACOES),
        base64.b64encode(salt).decode(),
        base64.b64encode(digest).decode(),
    ]
    return "$".join(partes)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        algoritmo, iteracoes, salt_b64, digest_b64 = senha_hash.split("$")
    except ValueError:
        return False
    if algoritmo != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", senha.encode(), base64.b64decode(salt_b64), int(iteracoes)
    )
    return hmac.compare_digest(digest, base64.b64decode(digest_b64))


def criar_token(sub: str, expira_em: timedelta | None = None) -> str:
    agora = datetime.now(UTC)
    expira = agora + (expira_em or timedelta(minutes=settings.token_expire_minutes))
    payload = {"sub": sub, "iat": agora, "exp": expira}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def ler_token(token: str) -> str | None:
    """Devolve o "sub" do token, ou None se for inválido ou expirado."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None
