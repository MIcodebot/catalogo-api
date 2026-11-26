from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.deps import Admin, DbSession
from app.models import Categoria, Produto
from app.schemas import Pagina, ProdutoAtualizar, ProdutoCriar, ProdutoSaida

router = APIRouter(prefix="/produtos", tags=["produtos"])


class Ordem(StrEnum):
    nome = "nome"
    preco = "preco"
    preco_desc = "-preco"
    recentes = "-criado_em"


_ORDENACAO = {
    Ordem.nome: Produto.nome.asc(),
    Ordem.preco: Produto.preco.asc(),
    Ordem.preco_desc: Produto.preco.desc(),
    Ordem.recentes: Produto.criado_em.desc(),
}


def _buscar(db: DbSession, produto_id: int) -> Produto:
    produto = db.get(Produto, produto_id, options=[joinedload(Produto.categoria)])
    if produto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produto não encontrado")
    return produto


def _checar_categoria(db: DbSession, categoria_id: int) -> None:
    if db.get(Categoria, categoria_id) is None:
        raise HTTPException(422, "Categoria inexistente")


@router.get("", response_model=Pagina)
def listar(
    db: DbSession,
    categoria: Annotated[str | None, Query(description="Slug da categoria")] = None,
    busca: Annotated[str | None, Query(min_length=2, description="Trecho do nome")] = None,
    disponivel: bool | None = None,
    preco_min: Annotated[Decimal | None, Query(ge=0)] = None,
    preco_max: Annotated[Decimal | None, Query(ge=0)] = None,
    ordem: Ordem = Ordem.nome,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    filtros = []
    if categoria:
        filtros.append(Categoria.slug == categoria)
    if busca:
        filtros.append(Produto.nome.ilike(f"%{busca}%"))
    if disponivel is not None:
        filtros.append(Produto.disponivel == disponivel)
    if preco_min is not None:
        filtros.append(Produto.preco >= preco_min)
    if preco_max is not None:
        filtros.append(Produto.preco <= preco_max)

    base = select(Produto).join(Produto.categoria).where(*filtros)
    total = db.scalar(select(func.count()).select_from(base.subquery()))
    itens = db.scalars(
        base.options(joinedload(Produto.categoria))
        .order_by(_ORDENACAO[ordem], Produto.id)
        .limit(limit)
        .offset(offset)
    ).all()
    return Pagina(total=total, limit=limit, offset=offset, itens=itens)


@router.get("/{produto_id}", response_model=ProdutoSaida)
def detalhar(produto_id: int, db: DbSession):
    return _buscar(db, produto_id)


@router.post("", response_model=ProdutoSaida, status_code=status.HTTP_201_CREATED)
def criar(dados: ProdutoCriar, db: DbSession, _: Admin):
    _checar_categoria(db, dados.categoria_id)
    produto = Produto(**dados.model_dump())
    db.add(produto)
    db.commit()
    return _buscar(db, produto.id)


@router.patch("/{produto_id}", response_model=ProdutoSaida)
def atualizar(produto_id: int, dados: ProdutoAtualizar, db: DbSession, _: Admin):
    produto = _buscar(db, produto_id)
    mudancas = dados.model_dump(exclude_unset=True)
    if mudancas.get("categoria_id") is not None:
        _checar_categoria(db, mudancas["categoria_id"])
    for campo, valor in mudancas.items():
        if valor is None and campo != "descricao":
            continue
        setattr(produto, campo, valor)
    db.commit()
    db.refresh(produto)
    return _buscar(db, produto_id)


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(produto_id: int, db: DbSession, _: Admin):
    db.delete(_buscar(db, produto_id))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
