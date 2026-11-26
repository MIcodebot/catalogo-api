from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.deps import Admin, DbSession
from app.models import Categoria, Produto
from app.schemas import CategoriaAtualizar, CategoriaCriar, CategoriaSaida

router = APIRouter(prefix="/categorias", tags=["categorias"])


def _buscar(db: DbSession, categoria_id: int) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria não encontrada")
    return categoria


def _salvar(db: DbSession, categoria: Categoria) -> Categoria:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Já existe uma categoria com esse slug"
        ) from None
    db.refresh(categoria)
    return categoria


@router.get("", response_model=list[CategoriaSaida])
def listar(db: DbSession):
    return db.scalars(select(Categoria).order_by(Categoria.nome)).all()


@router.get("/{categoria_id}", response_model=CategoriaSaida)
def detalhar(categoria_id: int, db: DbSession):
    return _buscar(db, categoria_id)


@router.post("", response_model=CategoriaSaida, status_code=status.HTTP_201_CREATED)
def criar(dados: CategoriaCriar, db: DbSession, _: Admin):
    categoria = Categoria(**dados.model_dump())
    db.add(categoria)
    return _salvar(db, categoria)


@router.patch("/{categoria_id}", response_model=CategoriaSaida)
def atualizar(categoria_id: int, dados: CategoriaAtualizar, db: DbSession, _: Admin):
    categoria = _buscar(db, categoria_id)
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(categoria, campo, valor)
    return _salvar(db, categoria)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover(categoria_id: int, db: DbSession, _: Admin):
    categoria = _buscar(db, categoria_id)
    em_uso = db.scalar(select(func.count()).where(Produto.categoria_id == categoria_id))
    if em_uso:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "A categoria tem produtos e não pode ser removida"
        )
    db.delete(categoria)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
