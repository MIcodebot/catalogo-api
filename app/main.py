from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import select

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Usuario
from app.routers import auth, categorias, produtos
from app.security import gerar_hash


def criar_admin_inicial() -> None:
    """Cria o usuário admin definido em ADMIN_EMAIL / ADMIN_PASSWORD, se ainda não existir."""
    if not (settings.admin_email and settings.admin_password):
        return
    with SessionLocal() as db:
        if db.scalar(select(Usuario).where(Usuario.email == settings.admin_email)) is None:
            db.add(
                Usuario(email=settings.admin_email, senha_hash=gerar_hash(settings.admin_password))
            )
            db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    criar_admin_inicial()
    yield


app = FastAPI(
    title="Catálogo API",
    description="API de catálogo de produtos para pequenos negócios.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(categorias.router)
app.include_router(produtos.router)


@app.get("/health", tags=["infra"])
def health() -> dict[str, str]:
    return {"status": "ok"}
