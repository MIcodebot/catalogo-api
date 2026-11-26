import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Usuario
from app.security import gerar_hash

ADMIN_EMAIL = "admin@exemplo.com"
ADMIN_SENHA = "senha-forte-123"


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    session.add(Usuario(email=ADMIN_EMAIL, senha_hash=gerar_hash(ADMIN_SENHA)))
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    # Sem "with": o lifespan (que usa o banco real) não roda nos testes.
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth(client):
    resposta = client.post("/auth/token", data={"username": ADMIN_EMAIL, "password": ADMIN_SENHA})
    token = resposta.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def categoria(client, auth):
    resposta = client.post("/categorias", json={"nome": "Cafés", "slug": "cafes"}, headers=auth)
    return resposta.json()
