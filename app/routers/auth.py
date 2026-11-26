from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.deps import DbSession
from app.models import Usuario
from app.schemas import Token
from app.security import criar_token, verificar_senha

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
def login(db: DbSession, form: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """Troca e-mail (campo "username") e senha por um token JWT."""
    usuario = db.scalar(select(Usuario).where(Usuario.email == form.username))
    if (
        usuario is None
        or not usuario.ativo
        or not verificar_senha(form.password, usuario.senha_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=criar_token(usuario.email))
