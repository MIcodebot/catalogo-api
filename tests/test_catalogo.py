import pytest


def criar_produto(client, auth, categoria_id, **extra):
    dados = {"nome": "Café coado", "preco": "8.50", "categoria_id": categoria_id} | extra
    r = client.post("/produtos", json=dados, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


# --- categorias ---------------------------------------------------------


def test_criar_e_listar_categorias(client, categoria):
    assert categoria["slug"] == "cafes"
    assert client.get("/categorias").json() == [categoria]


def test_slug_duplicado_retorna_409(client, auth, categoria):
    r = client.post("/categorias", json={"nome": "Outro", "slug": "cafes"}, headers=auth)
    assert r.status_code == 409


@pytest.mark.parametrize("slug", ["Com Espaco", "MAIUSCULO", "acento-é", "-comeca-com-hifen"])
def test_slug_invalido_retorna_422(client, auth, slug):
    r = client.post("/categorias", json={"nome": "X", "slug": slug}, headers=auth)
    assert r.status_code == 422


def test_atualizar_categoria(client, auth, categoria):
    r = client.patch(
        f"/categorias/{categoria['id']}", json={"nome": "Cafés especiais"}, headers=auth
    )
    assert r.status_code == 200
    assert r.json()["nome"] == "Cafés especiais"
    assert r.json()["slug"] == "cafes"


def test_nao_remove_categoria_com_produtos(client, auth, categoria):
    criar_produto(client, auth, categoria["id"])
    r = client.delete(f"/categorias/{categoria['id']}", headers=auth)
    assert r.status_code == 409


def test_remove_categoria_vazia(client, auth, categoria):
    assert client.delete(f"/categorias/{categoria['id']}", headers=auth).status_code == 204
    assert client.get(f"/categorias/{categoria['id']}").status_code == 404


# --- produtos -----------------------------------------------------------


def test_criar_produto(client, auth, categoria):
    p = criar_produto(client, auth, categoria["id"], descricao="Grão do sul de Minas")
    assert p["nome"] == "Café coado"
    assert p["preco"] == "8.50"
    assert p["categoria"]["slug"] == "cafes"
    assert client.get(f"/produtos/{p['id']}").json() == p


def test_produto_com_categoria_inexistente(client, auth):
    r = client.post(
        "/produtos", json={"nome": "X", "preco": "1.00", "categoria_id": 999}, headers=auth
    )
    assert r.status_code == 422


@pytest.mark.parametrize("preco", ["0", "-1", "1.999"])
def test_preco_invalido(client, auth, categoria, preco):
    r = client.post(
        "/produtos",
        json={"nome": "X", "preco": preco, "categoria_id": categoria["id"]},
        headers=auth,
    )
    assert r.status_code == 422


def test_atualizar_parcialmente(client, auth, categoria):
    p = criar_produto(client, auth, categoria["id"])
    r = client.patch(f"/produtos/{p['id']}", json={"preco": "9.90"}, headers=auth)
    assert r.status_code == 200
    assert r.json()["preco"] == "9.90"
    assert r.json()["nome"] == "Café coado"


def test_remover_produto(client, auth, categoria):
    p = criar_produto(client, auth, categoria["id"])
    assert client.delete(f"/produtos/{p['id']}", headers=auth).status_code == 204
    assert client.get(f"/produtos/{p['id']}").status_code == 404


def test_produto_inexistente(client):
    assert client.get("/produtos/123").status_code == 404


# --- listagem: filtros, ordenação e paginação ------------------------------


@pytest.fixture
def catalogo(client, auth, categoria):
    bolos = client.post("/categorias", json={"nome": "Bolos", "slug": "bolos"}, headers=auth).json()
    criar_produto(client, auth, categoria["id"], nome="Espresso", preco="6.00")
    criar_produto(client, auth, categoria["id"], nome="Cappuccino", preco="12.00")
    criar_produto(
        client, auth, categoria["id"], nome="Café gelado", preco="14.00", disponivel=False
    )
    criar_produto(client, auth, bolos["id"], nome="Bolo de cenoura", preco="10.00")
    criar_produto(client, auth, bolos["id"], nome="Bolo de fubá", preco="9.00")


def nomes(resposta):
    return [p["nome"] for p in resposta.json()["itens"]]


def test_lista_tudo_por_nome(client, catalogo):
    r = client.get("/produtos")
    assert r.json()["total"] == 5
    assert nomes(r) == ["Bolo de cenoura", "Bolo de fubá", "Café gelado", "Cappuccino", "Espresso"]


def test_filtra_por_categoria(client, catalogo):
    assert nomes(client.get("/produtos?categoria=bolos")) == ["Bolo de cenoura", "Bolo de fubá"]


def test_filtra_disponiveis(client, catalogo):
    r = client.get("/produtos?disponivel=true")
    assert r.json()["total"] == 4
    assert "Café gelado" not in nomes(r)


def test_busca_por_nome(client, catalogo):
    assert nomes(client.get("/produtos?busca=bolo")) == ["Bolo de cenoura", "Bolo de fubá"]


def test_faixa_de_preco(client, catalogo):
    r = client.get("/produtos?preco_min=9&preco_max=12&ordem=preco")
    assert nomes(r) == ["Bolo de fubá", "Bolo de cenoura", "Cappuccino"]


def test_ordem_preco_decrescente(client, catalogo):
    assert nomes(client.get("/produtos?ordem=-preco&limit=2")) == ["Café gelado", "Cappuccino"]


def test_paginacao(client, catalogo):
    r = client.get("/produtos?limit=2&offset=2")
    body = r.json()
    assert body["total"] == 5
    assert (body["limit"], body["offset"]) == (2, 2)
    assert nomes(r) == ["Café gelado", "Cappuccino"]


def test_limit_maximo(client):
    assert client.get("/produtos?limit=101").status_code == 422
