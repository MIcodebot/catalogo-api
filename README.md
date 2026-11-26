# Catálogo API

[![CI](https://github.com/MIcodebot/catalogo-api/actions/workflows/ci.yml/badge.svg)](https://github.com/MIcodebot/catalogo-api/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)

API REST de **catálogo de produtos para pequenos negócios** (cafés, restaurantes, lojas): o site do cliente consome os endpoints públicos para mostrar o cardápio ou o catálogo, e o dono do negócio usa os endpoints autenticados para cadastrar e atualizar produtos.

## Funcionalidades

- CRUD de **categorias** e **produtos**
- Listagem pública com **filtros** (categoria, disponibilidade, faixa de preço, busca por nome), **ordenação** e **paginação**
- **Autenticação JWT** (OAuth2 password flow) nas rotas de escrita
- Senhas com **PBKDF2-SHA256** e salt aleatório (biblioteca padrão)
- Regras de negócio: slug único (409), categoria com produtos não pode ser removida (409), preço positivo com 2 casas decimais (422)
- Documentação interativa automática em `/docs` (Swagger) e `/redoc`
- **34 testes** com pytest, ~95% de cobertura
- **CI** no GitHub Actions: lint (ruff), testes em Python 3.11, 3.12 e 3.13 e build da imagem Docker

## Stack

FastAPI · SQLAlchemy 2 · PostgreSQL (SQLite em desenvolvimento) · PyJWT · pytest · ruff · Docker

## Como rodar

### Com Docker (API + PostgreSQL)

```bash
cp .env.example .env      # ajuste SECRET_KEY, ADMIN_EMAIL e ADMIN_PASSWORD
docker compose up --build
```

A API sobe em http://localhost:8000 e a documentação em http://localhost:8000/docs.

### Localmente (SQLite)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export ADMIN_EMAIL=admin@exemplo.com ADMIN_PASSWORD=troque-esta-senha
uvicorn app.main:app --reload
```

Na primeira execução as tabelas são criadas e o usuário admin de `ADMIN_EMAIL` / `ADMIN_PASSWORD` é cadastrado.

## Exemplos

```bash
# Login
TOKEN=$(curl -s -X POST localhost:8000/auth/token \
  -d "username=admin@exemplo.com&password=troque-esta-senha" | jq -r .access_token)

# Criar categoria e produto
curl -X POST localhost:8000/categorias -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"nome": "Cafés", "slug": "cafes"}'

curl -X POST localhost:8000/produtos -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nome": "Espresso", "preco": "6.00", "categoria_id": 1}'

# Listagem pública com filtros
curl "localhost:8000/produtos?categoria=cafes&disponivel=true&ordem=preco&limit=10"
```

## Endpoints

| Método | Rota | Auth | Descrição |
|---|---|---|---|
| POST | `/auth/token` | | Login (retorna JWT) |
| GET | `/categorias` | | Lista categorias |
| GET | `/categorias/{id}` | | Detalha categoria |
| POST | `/categorias` | ✔ | Cria categoria |
| PATCH | `/categorias/{id}` | ✔ | Atualiza categoria |
| DELETE | `/categorias/{id}` | ✔ | Remove categoria vazia |
| GET | `/produtos` | | Lista com filtros, ordenação e paginação |
| GET | `/produtos/{id}` | | Detalha produto |
| POST | `/produtos` | ✔ | Cria produto |
| PATCH | `/produtos/{id}` | ✔ | Atualiza produto (parcial) |
| DELETE | `/produtos/{id}` | ✔ | Remove produto |
| GET | `/health` | | Healthcheck |

Parâmetros de `GET /produtos`: `categoria` (slug), `busca`, `disponivel`, `preco_min`, `preco_max`, `ordem` (`nome`, `preco`, `-preco`, `-criado_em`), `limit` (1–100) e `offset`.

## Estrutura

```
app/
├── main.py          # criação da app, lifespan e rotas
├── config.py        # configurações via variáveis de ambiente
├── database.py      # engine e sessão do SQLAlchemy
├── models.py        # modelos ORM
├── schemas.py       # validação de entrada/saída (Pydantic)
├── security.py      # hash de senha e JWT
├── deps.py          # dependências (sessão, usuário autenticado)
└── routers/         # auth, categorias, produtos
tests/               # pytest + TestClient com SQLite em memória
```

## Testes

```bash
pytest --cov=app
ruff check . && ruff format --check .
```

## Próximos passos

- [ ] Migrações com Alembic
- [ ] Upload de imagens dos produtos
- [ ] Vários negócios (multi-tenant) na mesma instância
- [ ] Deploy (Render / Fly.io)
