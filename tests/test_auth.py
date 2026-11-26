from datetime import timedelta

from app.security import criar_token, gerar_hash, ler_token, verificar_senha
from tests.conftest import ADMIN_EMAIL, ADMIN_SENHA


def test_hash_de_senha():
    h = gerar_hash("segredo")
    assert h != "segredo"
    assert verificar_senha("segredo", h)
    assert not verificar_senha("outra", h)


def test_hash_usa_salt_aleatorio():
    assert gerar_hash("segredo") != gerar_hash("segredo")


def test_hash_malformado_nao_quebra():
    assert not verificar_senha("x", "lixo")


def test_token_expirado_e_rejeitado():
    token = criar_token("a@b.com", expira_em=timedelta(seconds=-1))
    assert ler_token(token) is None


def test_login_ok(client):
    r = client.post("/auth/token", data={"username": ADMIN_EMAIL, "password": ADMIN_SENHA})
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert ler_token(r.json()["access_token"]) == ADMIN_EMAIL


def test_login_senha_errada(client):
    r = client.post("/auth/token", data={"username": ADMIN_EMAIL, "password": "errada"})
    assert r.status_code == 401


def test_rota_protegida_sem_token(client):
    r = client.post("/categorias", json={"nome": "X", "slug": "x"})
    assert r.status_code == 401


def test_rota_protegida_com_token_invalido(client):
    r = client.post(
        "/categorias", json={"nome": "X", "slug": "x"}, headers={"Authorization": "Bearer abc"}
    )
    assert r.status_code == 401
