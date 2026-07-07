"""
Testes para o router /admin:
  GET    /admin/read_gym_members
  GET    /admin/read_trainers
  POST   /admin/create_user
  PUT    /admin/edit_user/{user_id}
  GET    /admin/gym_member/{user_id}
  GET    /admin/trainer/{user_id}
  GET    /admin/gym_member/{user_id}/toggle_status
  POST   /admin/gym_member/{user_id}/exercises
  PUT    /admin/gym_member/{user_id}/edit_exercises/{exercise_id}
  DELETE /admin/gym_member/{user_id}/exercises/{exercise_id}
  DELETE /admin/gym_member/{user_id}/workout/{workout_type}
  POST   /admin/plans
  GET    /admin/plans
  GET    /admin/plans/{plan_id}
  PUT    /admin/plans/{plan_id}
  DELETE /admin/plans/{plan_id}
  PUT    /admin/plans/{plan_id}/activate
  GET    /admin/subscriptions
  GET    /admin/subscriptions/{user_id}
  PUT    /admin/subscriptions/{subscription_id}/cancel
  PUT    /admin/subscriptions/{subscription_id}/approve
"""

from tests.conftest import auth_header
from app.models.subscriptions import SubscriptionStatus


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
        "cpf": "69271586263",
        "password": "Trainer123!",
        "role": "aluno",
        "address": "Rua Treinador Novo, 40",
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
        "cpf": "26218388395",
        "password": "Trainer123!",
        "role": "treinador",
        "address": "Rua Duplicado, 50",
        "phone_number": "11944444444",
    }
    response = client.post("/admin/create_user", json=payload, headers=auth_header(admin_token))
    assert response.status_code == 409


def test_admin_create_user_forbidden_trainer(client, trainer_token):
    payload = {
        "name": "Tentativa",
        "email": "tentativa@test.com",
        "cpf": "49860003653",
        "password": "Senha123!",
        "role": "treinador",
        "address": "Rua Tentativa, 60",
        "phone_number": "11933333333",
    }
    response = client.post("/admin/create_user", json=payload, headers=auth_header(trainer_token))
    assert response.status_code == 403


def test_admin_create_user_forbidden_member(client, member_token):
    payload = {
        "name": "Tentativa",
        "email": "tentativa@test.com",
        "cpf": "60067140432",
        "password": "Senha123!",
        "role": "treinador",
        "address": "Rua Tentativa, 70",
        "phone_number": "11933333333",
    }
    response = client.post("/admin/create_user", json=payload, headers=auth_header(member_token))
    assert response.status_code == 403


# ── PUT /admin/edit_user/{user_id} ────────────────────────────────────────────
# Observação: a rota exige reenviar a senha atual no payload (usa o schema de
# criação de usuário) e não retorna o usuário atualizado no corpo da resposta.

def test_edit_user_success(client, admin_token, member_user, db):
    payload = {
        "name": "Aluno Editado",
        "email": "aluno_editado@test.com",
        "cpf": "27627682509",
        "password": "Member123!",
        "role": "aluno",
        "address": "Rua Editada, 80",
        "phone_number": "11900011122",
    }
    response = client.put(
        f"/admin/edit_user/{member_user.id}",
        json=payload,
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200

    db.refresh(member_user)
    assert member_user.name == "Aluno Editado"
    assert member_user.email == "aluno_editado@test.com"
    assert member_user.cpf == "27627682509"
    assert member_user.address == "Rua Editada, 80"
    assert member_user.phone_number == "11900011122"


def test_edit_user_not_found(client, admin_token):
    payload = {
        "name": "Ninguem",
        "email": "ninguem@test.com",
        "cpf": "82010075900",
        "password": "Senha123!",
        "role": "aluno",
        "address": "Rua Ninguem, 90",
        "phone_number": "11900011123",
    }
    response = client.put(
        "/admin/edit_user/99999",
        json=payload,
        headers=auth_header(admin_token),
    )
    assert response.status_code == 404


def test_edit_user_forbidden(client, trainer_token, member_user):
    payload = {
        "name": "Aluno Editado",
        "email": "aluno_editado2@test.com",
        "cpf": "27627682509",
        "password": "Member123!",
        "role": "aluno",
        "address": "Rua Editada, 80",
        "phone_number": "11900011122",
    }
    response = client.put(
        f"/admin/edit_user/{member_user.id}",
        json=payload,
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 404  # admin router retorna 404 para acesso negado


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


# ── POST /admin/plans ──────────────────────────────────────────────────────────

def test_create_plan_success(client, admin_token, mock_mercado_pago, db):
    from app.models.plans import Plan

    payload = {
        "name": "Plano Mensal",
        "description": "Acesso completo",
        "price": 99.9,
        "duration_days": 30,
    }
    response = client.post("/admin/plans", json=payload, headers=auth_header(admin_token))
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Plano Mensal"
    assert body["mercado_pago_plan_id"] == "mp-plan-123"

    plan = db.query(Plan).filter(Plan.name == "Plano Mensal").first()
    assert plan is not None


def test_create_plan_duplicate_name(client, admin_token, mock_mercado_pago, sample_plan):
    payload = {
        "name": sample_plan.name,
        "description": "Outro",
        "price": 50.0,
        "duration_days": 30,
    }
    response = client.post("/admin/plans", json=payload, headers=auth_header(admin_token))
    assert response.status_code == 400
    assert "Já existe" in response.json()["detail"]


def test_create_plan_mercado_pago_error(client, admin_token, monkeypatch):
    from app.services.mercado_pago import mercado_pago_service

    def raise_error(*args, **kwargs):
        raise Exception("timeout")

    monkeypatch.setattr(mercado_pago_service, "create_plan", raise_error)

    payload = {
        "name": "Plano com erro",
        "description": "desc",
        "price": 50.0,
        "duration_days": 30,
    }
    response = client.post("/admin/plans", json=payload, headers=auth_header(admin_token))
    assert response.status_code == 400
    assert "Erro ao criar plano" in response.json()["detail"]


def test_create_plan_forbidden(client, trainer_token, mock_mercado_pago):
    payload = {
        "name": "Plano Proibido",
        "description": "desc",
        "price": 50.0,
        "duration_days": 30,
    }
    response = client.post("/admin/plans", json=payload, headers=auth_header(trainer_token))
    assert response.status_code == 403


# ── GET /admin/plans ────────────────────────────────────────────────────────────

def test_get_all_plans_success(client, admin_token, sample_plan):
    response = client.get("/admin/plans", headers=auth_header(admin_token))
    assert response.status_code == 201
    names = [p["name"] for p in response.json()]
    assert sample_plan.name in names


def test_get_all_plans_empty(client, admin_token):
    response = client.get("/admin/plans", headers=auth_header(admin_token))
    assert response.status_code == 404


def test_get_all_plans_forbidden(client, trainer_token, sample_plan):
    response = client.get("/admin/plans", headers=auth_header(trainer_token))
    assert response.status_code == 403


# ── GET /admin/plans/{plan_id} ───────────────────────────────────────────────────

def test_get_plan_by_id_success(client, admin_token, sample_plan):
    response = client.get(f"/admin/plans/{sample_plan.id}", headers=auth_header(admin_token))
    assert response.status_code == 200
    assert response.json()["name"] == sample_plan.name


def test_get_plan_by_id_not_found(client, admin_token):
    response = client.get("/admin/plans/99999", headers=auth_header(admin_token))
    assert response.status_code == 404


# ── PUT /admin/plans/{plan_id} ───────────────────────────────────────────────────

def test_update_plan_success(client, admin_token, sample_plan, db):
    payload = {
        "name": "Plano Atualizado",
        "description": "Nova descrição",
        "price": 149.9,
        "duration_days": 60,
    }
    response = client.put(
        f"/admin/plans/{sample_plan.id}", json=payload, headers=auth_header(admin_token)
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Plano Atualizado"
    assert body["price"] == 149.9
    assert body["duration_days"] == 60


def test_update_plan_not_found(client, admin_token):
    payload = {
        "name": "X",
        "description": "Y",
        "price": 10.0,
        "duration_days": 30,
    }
    response = client.put("/admin/plans/99999", json=payload, headers=auth_header(admin_token))
    assert response.status_code == 404


# ── DELETE /admin/plans/{plan_id} ────────────────────────────────────────────────

def test_deactivate_plan_success(client, admin_token, sample_plan, db):
    response = client.delete(f"/admin/plans/{sample_plan.id}", headers=auth_header(admin_token))
    assert response.status_code == 200
    assert "desativado" in response.json()["message"]

    db.refresh(sample_plan)
    assert sample_plan.active is False


def test_deactivate_plan_already_inactive(client, admin_token, inactive_plan):
    response = client.delete(f"/admin/plans/{inactive_plan.id}", headers=auth_header(admin_token))
    assert response.status_code == 400


def test_deactivate_plan_not_found(client, admin_token):
    response = client.delete("/admin/plans/99999", headers=auth_header(admin_token))
    assert response.status_code == 404


# ── PUT /admin/plans/{plan_id}/activate ─────────────────────────────────────────

def test_activate_plan_success(client, admin_token, inactive_plan, db):
    response = client.put(
        f"/admin/plans/{inactive_plan.id}/activate", headers=auth_header(admin_token)
    )
    assert response.status_code == 200
    assert "ativo" in response.json()["message"]

    db.refresh(inactive_plan)
    assert inactive_plan.active is True


def test_activate_plan_already_active(client, admin_token, sample_plan):
    response = client.put(
        f"/admin/plans/{sample_plan.id}/activate", headers=auth_header(admin_token)
    )
    assert response.status_code == 400


def test_activate_plan_not_found(client, admin_token):
    response = client.put("/admin/plans/99999/activate", headers=auth_header(admin_token))
    assert response.status_code == 404


# ── GET /admin/subscriptions ─────────────────────────────────────────────────────

def test_get_all_subscriptions_success(client, admin_token, pending_subscription, member_user):
    response = client.get("/admin/subscriptions", headers=auth_header(admin_token))
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["student_email"] == member_user.email
    assert body[0]["status"] == "pending"


def test_get_all_subscriptions_empty(client, admin_token):
    response = client.get("/admin/subscriptions", headers=auth_header(admin_token))
    assert response.status_code == 404


def test_get_all_subscriptions_forbidden(client, trainer_token):
    response = client.get("/admin/subscriptions", headers=auth_header(trainer_token))
    assert response.status_code == 403


# ── GET /admin/subscriptions/{user_id} ───────────────────────────────────────────

def test_get_subscription_by_user_success(client, admin_token, pending_subscription, member_user):
    response = client.get(
        f"/admin/subscriptions/{member_user.id}", headers=auth_header(admin_token)
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_get_subscription_by_user_not_found(client, admin_token, member_user):
    response = client.get(
        f"/admin/subscriptions/{member_user.id}", headers=auth_header(admin_token)
    )
    assert response.status_code == 404


# ── PUT /admin/subscriptions/{subscription_id}/cancel ────────────────────────────

def test_cancel_subscription_success(client, admin_token, pending_subscription, db):
    response = client.put(
        f"/admin/subscriptions/{pending_subscription.id}/cancel",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    db.refresh(pending_subscription)
    assert pending_subscription.status == SubscriptionStatus.cancelled


def test_cancel_subscription_already_cancelled(client, admin_token, pending_subscription):
    client.put(
        f"/admin/subscriptions/{pending_subscription.id}/cancel",
        headers=auth_header(admin_token),
    )
    response = client.put(
        f"/admin/subscriptions/{pending_subscription.id}/cancel",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 400


def test_cancel_subscription_not_found(client, admin_token):
    response = client.put("/admin/subscriptions/99999/cancel", headers=auth_header(admin_token))
    assert response.status_code == 404


def test_cancel_subscription_forbidden(client, trainer_token, pending_subscription):
    response = client.put(
        f"/admin/subscriptions/{pending_subscription.id}/cancel",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 403


# ── PUT /admin/subscriptions/{subscription_id}/approve ───────────────────────────

def test_approve_subscription_success(client, admin_token, pending_subscription, sample_plan, db):
    response = client.put(
        f"/admin/subscriptions/{pending_subscription.id}/approve",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["started_at"] is not None
    assert body["expires_at"] is not None

    db.refresh(pending_subscription)
    assert pending_subscription.status == SubscriptionStatus.approved
    assert pending_subscription.next_billing_at == pending_subscription.expires_at


def test_approve_subscription_already_approved(client, admin_token, pending_subscription):
    client.put(
        f"/admin/subscriptions/{pending_subscription.id}/approve",
        headers=auth_header(admin_token),
    )
    response = client.put(
        f"/admin/subscriptions/{pending_subscription.id}/approve",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 400


def test_approve_subscription_not_found(client, admin_token):
    response = client.put("/admin/subscriptions/99999/approve", headers=auth_header(admin_token))
    assert response.status_code == 404


def test_approve_subscription_forbidden(client, trainer_token, pending_subscription):
    response = client.put(
        f"/admin/subscriptions/{pending_subscription.id}/approve",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 403
