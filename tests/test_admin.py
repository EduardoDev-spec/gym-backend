"""
Testes para o router /admin:
  GET    /admin/read_gym_members
  GET    /admin/read_trainers
  POST   /admin/create_user
  GET    /admin/gym_member/{user_id}
  GET    /admin/trainer/{user_id}
  GET    /admin/gym_member/{user_id}/toggle_status
  POST   /admin/gym_member/{user_id}/exercises
  PUT    /admin/gym_member/{user_id}/edit_exercises/{exercise_id}
  DELETE /admin/gym_member/{user_id}/exercises/{exercise_id}
  DELETE /admin/gym_member/{user_id}/workout/{workout_type}
"""

from tests.conftest import auth_header


# ── GET /admin/read_gym_members ───────────────────────────────────────────────

def test_read_gym_members_success(client, admin_user, admin_token, member_user):
    response = client.get("/admin/read_gym_members", headers=auth_header(admin_token))
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert member_user.email in emails


def test_read_gym_members_does_not_return_trainers(client, admin_token, trainer_user, member_user):
    response = client.get("/admin/read_gym_members", headers=auth_header(admin_token))
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert trainer_user.email not in emails


def test_read_gym_members_filter_by_name(client, admin_token, member_user):
    response = client.get(
        f"/admin/read_gym_members?name={member_user.name[:5]}",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_read_gym_members_filter_no_match(client, admin_token, member_user):
    response = client.get(
        "/admin/read_gym_members?name=NomeQueNaoExiste",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert response.json() == []


def test_read_gym_members_forbidden_trainer(client, trainer_token, member_user):
    response = client.get("/admin/read_gym_members", headers=auth_header(trainer_token))
    assert response.status_code == 403


def test_read_gym_members_forbidden_member(client, member_token, member_user):
    response = client.get("/admin/read_gym_members", headers=auth_header(member_token))
    assert response.status_code == 403


def test_read_gym_members_unauthenticated(client):
    response = client.get("/admin/read_gym_members")
    assert response.status_code == 401


# ── GET /admin/read_trainers ──────────────────────────────────────────────────

def test_read_trainers_success(client, admin_token, trainer_user):
    response = client.get("/admin/read_trainers", headers=auth_header(admin_token))
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert trainer_user.email in emails


def test_read_trainers_does_not_return_members(client, admin_token, trainer_user, member_user):
    response = client.get("/admin/read_trainers", headers=auth_header(admin_token))
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert member_user.email not in emails


def test_read_trainers_forbidden(client, trainer_token):
    response = client.get("/admin/read_trainers", headers=auth_header(trainer_token))
    assert response.status_code == 403


# ── POST /admin/create_user ───────────────────────────────────────────────────

def test_admin_create_user_success(client, admin_token, db):
    from app.models.users import User, UserRole

    payload = {
        "name": "Novo Treinador",
        "email": "novo_trainer@test.com",
        "password": "Trainer123!",
        "role": "aluno",
        "phone_number": "11955555555",
    }
    response = client.post("/admin/create_user", json=payload, headers=auth_header(admin_token))
    assert response.status_code == 201
    assert "criado com sucesso" in response.json()["message"]

    # admin/create_user sempre cria com role=trainer
    user = db.query(User).filter(User.email == "novo_trainer@test.com").first()
    assert user is not None
    assert user.role == UserRole.trainer


def test_admin_create_user_duplicate_email(client, admin_token, trainer_user):
    payload = {
        "name": "Duplicado",
        "email": trainer_user.email,
        "password": "Trainer123!",
        "role": "treinador",
        "phone_number": "11944444444",
    }
    response = client.post("/admin/create_user", json=payload, headers=auth_header(admin_token))
    assert response.status_code == 409


def test_admin_create_user_forbidden_trainer(client, trainer_token):
    payload = {
        "name": "Tentativa",
        "email": "tentativa@test.com",
        "password": "Senha123!",
        "role": "treinador",
        "phone_number": "11933333333",
    }
    response = client.post("/admin/create_user", json=payload, headers=auth_header(trainer_token))
    assert response.status_code == 403


def test_admin_create_user_forbidden_member(client, member_token):
    payload = {
        "name": "Tentativa",
        "email": "tentativa@test.com",
        "password": "Senha123!",
        "role": "treinador",
        "phone_number": "11933333333",
    }
    response = client.post("/admin/create_user", json=payload, headers=auth_header(member_token))
    assert response.status_code == 403


# ── GET /admin/gym_member/{user_id} ──────────────────────────────────────────

def test_get_gym_member_by_id_success(client, admin_token, member_user):
    response = client.get(
        f"/admin/gym_member/{member_user.id}",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["email"] == member_user.email


def test_get_gym_member_by_id_not_found(client, admin_token):
    response = client.get("/admin/gym_member/99999", headers=auth_header(admin_token))
    assert response.status_code == 404


def test_get_gym_member_by_id_returns_404_for_trainer_id(client, admin_token, trainer_user):
    # Verifica que buscar um treinador na rota de aluno retorna 404
    response = client.get(
        f"/admin/gym_member/{trainer_user.id}",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 404


def test_get_gym_member_by_id_forbidden(client, trainer_token, member_user):
    response = client.get(
        f"/admin/gym_member/{member_user.id}",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 403


# ── GET /admin/trainer/{user_id} ─────────────────────────────────────────────

def test_get_trainer_by_id_success(client, admin_token, trainer_user):
    response = client.get(
        f"/admin/trainer/{trainer_user.id}",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["email"] == trainer_user.email


def test_get_trainer_by_id_not_found(client, admin_token):
    response = client.get("/admin/trainer/99999", headers=auth_header(admin_token))
    assert response.status_code == 404


def test_get_trainer_by_id_returns_404_for_member_id(client, admin_token, member_user):
    response = client.get(
        f"/admin/trainer/{member_user.id}",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 404


# ── GET /admin/gym_member/{user_id}/toggle_status ────────────────────────────

def test_toggle_status_deactivates_active_member(client, admin_token, member_user, db):
    from app.models.users import User

    assert member_user.is_active is True

    response = client.get(
        f"/admin/gym_member/{member_user.id}/toggle_status",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert "Bloqueado" in response.json()["message"]

    db.refresh(member_user)
    assert member_user.is_active is False


def test_toggle_status_reactivates_inactive_member(client, admin_token, inactive_member, db):
    from app.models.users import User

    assert inactive_member.is_active is False

    response = client.get(
        f"/admin/gym_member/{inactive_member.id}/toggle_status",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert "Ativo" in response.json()["message"]

    db.refresh(inactive_member)
    assert inactive_member.is_active is True


def test_toggle_status_not_found(client, admin_token):
    response = client.get(
        "/admin/gym_member/99999/toggle_status",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 404


def test_toggle_status_forbidden(client, trainer_token, member_user):
    response = client.get(
        f"/admin/gym_member/{member_user.id}/toggle_status",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 403


# ── POST /admin/gym_member/{user_id}/exercises ───────────────────────────────

EXERCISES_PAYLOAD = [
    {
        "name_exercises": "Supino Reto",
        "workout_type": "A",
        "sets": 3,
        "reps": 10,
        "weight": "80kg",
    },
    {
        "name_exercises": "Agachamento",
        "workout_type": "A",
        "sets": 4,
        "reps": 12,
        "weight": "100kg",
    },
]


def test_create_exercises_for_member_success(client, admin_token, member_user):
    response = client.post(
        f"/admin/gym_member/{member_user.id}/exercises",
        json=EXERCISES_PAYLOAD,
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert "2 exercícios" in response.json()["message"]


def test_create_exercises_member_not_found(client, admin_token):
    response = client.post(
        "/admin/gym_member/99999/exercises",
        json=EXERCISES_PAYLOAD,
        headers=auth_header(admin_token),
    )
    assert response.status_code == 404


def test_create_exercises_forbidden(client, trainer_token, member_user):
    response = client.post(
        f"/admin/gym_member/{member_user.id}/exercises",
        json=EXERCISES_PAYLOAD,
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 403


# ── PUT /admin/gym_member/{user_id}/edit_exercises/{exercise_id} ──────────────

def test_edit_exercise_success(client, admin_token, member_user, sample_exercise):
    payload = {
        "name_exercises": "Supino Inclinado",
        "workout_type": "B",
        "sets": 4,
        "reps": 8,
        "weight": "90kg",
    }
    response = client.put(
        f"/admin/gym_member/{member_user.id}/edit_exercises/{sample_exercise.id}",
        json=payload,
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200


def test_edit_exercise_not_found(client, admin_token, member_user):
    payload = {
        "name_exercises": "X",
        "workout_type": "B",
        "sets": 1,
        "reps": 1,
        "weight": None,
    }
    response = client.put(
        f"/admin/gym_member/{member_user.id}/edit_exercises/99999",
        json=payload,
        headers=auth_header(admin_token),
    )
    assert response.status_code == 404


def test_edit_exercise_forbidden(client, trainer_token, member_user, sample_exercise):
    payload = {
        "name_exercises": "X",
        "workout_type": "B",
        "sets": 1,
        "reps": 1,
        "weight": None,
    }
    response = client.put(
        f"/admin/gym_member/{member_user.id}/edit_exercises/{sample_exercise.id}",
        json=payload,
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 404  # admin router retorna 404 para acesso negado


# ── DELETE /admin/gym_member/{user_id}/exercises/{exercise_id} ────────────────

def test_delete_exercise_success(client, admin_token, member_user, sample_exercise, db):
    from app.models.exercises import Exercises

    response = client.delete(
        f"/admin/gym_member/{member_user.id}/exercises/{sample_exercise.id}",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200

    deleted = db.query(Exercises).filter(Exercises.id == sample_exercise.id).first()
    assert deleted is None


def test_delete_exercise_not_found(client, admin_token, member_user):
    response = client.delete(
        f"/admin/gym_member/{member_user.id}/exercises/99999",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 404


def test_delete_exercise_wrong_user(client, admin_token, admin_user, sample_exercise):
    # Exercício pertence a member_user, mas buscamos pelo id do admin
    response = client.delete(
        f"/admin/gym_member/{admin_user.id}/exercises/{sample_exercise.id}",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 404


# ── DELETE /admin/gym_member/{user_id}/workout/{workout_type} ─────────────────

def test_delete_workout_success(client, admin_token, member_user, sample_exercise, db):
    from app.models.exercises import Exercises

    response = client.delete(
        f"/admin/gym_member/{member_user.id}/workout/A",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200

    remaining = (
        db.query(Exercises)
        .filter(Exercises.user_id == member_user.id, Exercises.workout_type == "A")
        .all()
    )
    assert remaining == []


def test_delete_workout_not_found(client, admin_token, member_user):
    response = client.delete(
        f"/admin/gym_member/{member_user.id}/workout/Z",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 404


def test_delete_workout_forbidden(client, trainer_token, member_user, sample_exercise):
    response = client.delete(
        f"/admin/gym_member/{member_user.id}/workout/A",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 404  # admin router retorna 404 para acesso negado
