"""
Testes para o router /user:
  GET /user/me
"""

from tests.conftest import auth_header


def test_get_me_success(client, member_user, member_token):
    response = client.get("/user/me", headers=auth_header(member_token))
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == member_user.email
    assert body["name"] == member_user.name


def test_get_me_as_admin(client, admin_user, admin_token):
    response = client.get("/user/me", headers=auth_header(admin_token))
    assert response.status_code == 200
    assert response.json()["email"] == admin_user.email


def test_get_me_as_trainer(client, trainer_user, trainer_token):
    response = client.get("/user/me", headers=auth_header(trainer_token))
    assert response.status_code == 200
    assert response.json()["email"] == trainer_user.email


def test_get_me_unauthenticated(client):
    response = client.get("/user/me")
    assert response.status_code == 401
