"""
Testes para o router /auth:
  POST /auth/create_user
  POST /auth/token
  PUT  /auth/change_password
"""

from tests.conftest import auth_header, make_token


# ── POST /auth/create_user ─────────────────────────────────────────────────────

def test_create_user_success(client):
    payload = {
        "name": "Novo Aluno",
        "email": "novo@test.com",
        "password": "Senha123!",
        "role": "aluno",
        "phone_number": "11911111111",
    }
    response = client.post("/auth/create_user", json=payload)
    assert response.status_code == 201


def test_create_user_duplicate_email(client, member_user):
    payload = {
        "name": "Outro Aluno",
        "email": member_user.email,
        "password": "Senha123!",
        "role": "aluno",
        "phone_number": "11922222222",
    }
    response = client.post("/auth/create_user", json=payload)
    assert response.status_code == 400
    assert "já está em uso" in response.json()["detail"]


def test_create_user_always_creates_as_gym_member(client, db):
    from app.models.users import User, UserRole

    payload = {
        "name": "Tentativa Admin",
        "email": "fake_admin@test.com",
        "password": "Senha123!",
        "role": "admin",
        "phone_number": "11933333333",
    }
    response = client.post("/auth/create_user", json=payload)
    assert response.status_code == 201

    user = db.query(User).filter(User.email == "fake_admin@test.com").first()
    assert user.role == UserRole.gym_member


# ── POST /auth/token ───────────────────────────────────────────────────────────

def test_login_success(client, member_user):
    response = client.post(
        "/auth/token",
        data={"username": member_user.email, "password": "Member123!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client, member_user):
    response = client.post(
        "/auth/token",
        data={"username": member_user.email, "password": "SenhaErrada"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/token",
        data={"username": "naoexiste@test.com", "password": "Qualquer123!"},
    )
    assert response.status_code == 401


def test_login_inactive_user(client, inactive_member):
    response = client.post(
        "/auth/token",
        data={"username": inactive_member.email, "password": "Inactive123!"},
    )
    assert response.status_code == 401


# ── PUT /auth/change_password ─────────────────────────────────────────────────

def test_change_password_success(client, member_user, member_token):
    payload = {
        "current_password": "Member123!",
        "new_password": "NovaSenha123!",
        "confirm_password": "NovaSenha123!",
    }
    response = client.put(
        "/auth/change_password",
        json=payload,
        headers=auth_header(member_token),
    )
    assert response.status_code == 200
    assert "sucesso" in response.json()["message"]


def test_change_password_wrong_current(client, member_user, member_token):
    payload = {
        "current_password": "SenhaErrada",
        "new_password": "NovaSenha123!",
        "confirm_password": "NovaSenha123!",
    }
    response = client.put(
        "/auth/change_password",
        json=payload,
        headers=auth_header(member_token),
    )
    assert response.status_code == 400
    assert "Senha incorreta" in response.json()["detail"]


def test_change_password_mismatch(client, member_user, member_token):
    payload = {
        "current_password": "Member123!",
        "new_password": "NovaSenha123!",
        "confirm_password": "SenhaDiferente!",
    }
    response = client.put(
        "/auth/change_password",
        json=payload,
        headers=auth_header(member_token),
    )
    assert response.status_code == 400
    assert "não coincidem" in response.json()["detail"]


def test_change_password_same_as_current(client, member_user, member_token):
    payload = {
        "current_password": "Member123!",
        "new_password": "Member123!",
        "confirm_password": "Member123!",
    }
    response = client.put(
        "/auth/change_password",
        json=payload,
        headers=auth_header(member_token),
    )
    assert response.status_code == 400
    assert "diferente" in response.json()["detail"]


def test_change_password_unauthenticated(client):
    payload = {
        "current_password": "Member123!",
        "new_password": "NovaSenha123!",
        "confirm_password": "NovaSenha123!",
    }
    response = client.put("/auth/change_password", json=payload)
    assert response.status_code == 401
