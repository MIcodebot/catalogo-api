from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.security import ler_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

DbSession = Annotated[Session, Depends(get_db)]


def usuario_atual(db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]) -> Usuario:
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = ler_token(token)
    if email is None:
        raise credenciais_invalidas
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    if usuario is None or not usuario.ativo:
        raise credenciais_invalidas
    return usuario


Admin = Annotated[Usuario, Depends(usuario_atual)]
