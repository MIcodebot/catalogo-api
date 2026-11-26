from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CategoriaCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=100, pattern=SLUG_PATTERN)


class CategoriaAtualizar(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=100, pattern=SLUG_PATTERN)


class CategoriaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    slug: str


class ProdutoCriar(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    descricao: str | None = None
    preco: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    disponivel: bool = True
    categoria_id: int


class ProdutoAtualizar(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=150)
    descricao: str | None = None
    preco: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    disponivel: bool | None = None
    categoria_id: int | None = None


class ProdutoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None
    preco: Decimal
    disponivel: bool
    categoria: CategoriaSaida
    criado_em: datetime
    atualizado_em: datetime

    @field_validator("criado_em", "atualizado_em")
    @classmethod
    def _em_utc(cls, valor: datetime) -> datetime:
        # SQLite não guarda fuso; os valores são sempre gravados em UTC.
        return valor if valor.tzinfo else valor.replace(tzinfo=UTC)


class Pagina(BaseModel):
    total: int
    limit: int
    offset: int
    itens: list[ProdutoSaida]
