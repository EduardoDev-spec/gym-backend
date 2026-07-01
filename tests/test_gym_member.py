"""
Testes para o router /gym_member:
  GET /gym_member/workout/{workout_type}
  POST /gym_member/start_workout
  PUT  /gym_member/finish_workout/{session_id}
  PUT  /gym_member/complete_exercise/{workout_exercise_id}
"""

from tests.conftest import auth_header


# ── GET /gym_member/workout/{workout_type} ────────────────────────────────────

def test_get_workout_success(client, member_token, member_user, sample_exercise):
    response = client.get("/gym_member/workout/A", headers=auth_header(member_token))
    assert response.status_code == 200
    exercises = response.json()
    assert len(exercises) >= 1
    assert exercises[0]["workout_type"] == "A"


def test_get_workout_only_returns_own_exercises(client, member_token, db, member_user):
    from app.models.users import User, UserRole
    from app.models.exercises import Exercises

    # Outro aluno com exercício no mesmo tipo de treino
    other = User(
        name="Outro Aluno",
        email="outro@test.com",
        hashed_password="hash",
        role=UserRole.gym_member,
        phone_number="11900000000",
        is_active=True,
    )
    db.add(other)
    db.commit()
    db.refresh(other)

    other_ex = Exercises(
        name_exercises="Leg Press",
        workout_type="A",
        sets=3,
        reps=15,
        weight="120kg",
        user_id=other.id,
    )
    db.add(other_ex)
    db.commit()

    ex_mine = Exercises(
        name_exercises="Supino",
        workout_type="A",
        sets=3,
        reps=10,
        weight="80kg",
        user_id=member_user.id,
    )
    db.add(ex_mine)
    db.commit()

    response = client.get("/gym_member/workout/A", headers=auth_header(member_token))
    assert response.status_code == 200
    ids = [e["user_id"] for e in response.json()]
    assert all(i == member_user.id for i in ids)


def test_get_workout_not_found(client, member_token, member_user):
    # Aluno sem exercícios no treino B
    response = client.get("/gym_member/workout/B", headers=auth_header(member_token))
    assert response.status_code == 404


def test_get_workout_forbidden_admin(client, admin_token):
    response = client.get("/gym_member/workout/A", headers=auth_header(admin_token))
    assert response.status_code == 403


def test_get_workout_forbidden_trainer(client, trainer_token):
    response = client.get("/gym_member/workout/A", headers=auth_header(trainer_token))
    assert response.status_code == 403


def test_get_workout_unauthenticated(client):
    response = client.get("/gym_member/workout/A")
    assert response.status_code == 401


# ── POST /gym_member/start_workout ────────────────────────────────────────────

def test_start_workout_success(client, member_token, member_user, sample_exercise):
    response = client.post(
        "/gym_member/start_workout",
        json={"workout_type": "A"},
        headers=auth_header(member_token),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["user_id"] == member_user.id
    assert body["workout_type"] == "A"
    assert body["status"] == "começou"
    assert body["finished_at"] is None


def test_start_workout_no_exercises(client, member_token, member_user):
    # Aluno sem exercícios no treino B
    response = client.post(
        "/gym_member/start_workout",
        json={"workout_type": "B"},
        headers=auth_header(member_token),
    )
    assert response.status_code == 404
    assert "Treino não encontrado" in response.json()["detail"]


def test_start_workout_already_started(client, member_token, member_user, started_session):
    # Já existe uma sessão em andamento
    response = client.post(
        "/gym_member/start_workout",
        json={"workout_type": "A"},
        headers=auth_header(member_token),
    )
    assert response.status_code == 400
    assert "em andamento" in response.json()["detail"]


def test_start_workout_forbidden_trainer(client, trainer_token):
    response = client.post(
        "/gym_member/start_workout",
        json={"workout_type": "A"},
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 403


def test_start_workout_forbidden_admin(client, admin_token):
    response = client.post(
        "/gym_member/start_workout",
        json={"workout_type": "A"},
        headers=auth_header(admin_token),
    )
    assert response.status_code == 403


# ── PUT /gym_member/finish_workout/{session_id} ───────────────────────────────

def test_finish_workout_success(client, member_token, member_user, started_session):
    session_id = started_session["session"].id
    response = client.put(
        f"/gym_member/finish_workout/{session_id}",
        headers=auth_header(member_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "finalizou"
    assert body["finished_at"] is not None


def test_finish_workout_already_finished(client, member_token, member_user, started_session, db):
    from app.models.workout_session import WorkoutSession, SessionStatus

    session_id = started_session["session"].id

    # Finaliza pela primeira vez
    client.put(
        f"/gym_member/finish_workout/{session_id}",
        headers=auth_header(member_token),
    )

    # Tenta finalizar novamente
    response = client.put(
        f"/gym_member/finish_workout/{session_id}",
        headers=auth_header(member_token),
    )
    assert response.status_code == 400
    assert "já foi finalizada" in response.json()["detail"]


def test_finish_workout_not_found(client, member_token):
    response = client.put(
        "/gym_member/finish_workout/99999",
        headers=auth_header(member_token),
    )
    assert response.status_code == 404


def test_finish_workout_cannot_finish_another_members_session(
    client, db, member_user, sample_exercise
):
    from app.models.users import User, UserRole
    from app.models.workout_session import WorkoutSession, SessionStatus
    from tests.conftest import make_token

    # Cria outro aluno com uma sessão
    other = User(
        name="Outro Aluno",
        email="outro2@test.com",
        hashed_password="hash",
        role=UserRole.gym_member,
        phone_number="11800000001",
        is_active=True,
    )
    db.add(other)
    db.commit()
    db.refresh(other)

    session = WorkoutSession(
        user_id=other.id,
        workout_type="A",
        status=SessionStatus.started,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # member_user tenta finalizar sessão do outro aluno
    member_token = make_token(member_user.id, member_user.email, member_user.role)
    response = client.put(
        f"/gym_member/finish_workout/{session.id}",
        headers=auth_header(member_token),
    )
    assert response.status_code == 404


def test_finish_workout_forbidden_trainer(client, trainer_token, started_session):
    session_id = started_session["session"].id
    response = client.put(
        f"/gym_member/finish_workout/{session_id}",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 403


# ── PUT /gym_member/complete_exercise/{workout_exercise_id} ──────────────────

def test_complete_exercise_success(client, member_token, started_session):
    we_id = started_session["workout_exercise"].id
    response = client.put(
        f"/gym_member/complete_exercise/{we_id}",
        json={"used_weight": 82.5},
        headers=auth_header(member_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Exercício concluído com sucesso."
    assert body["exercise"]["completed"] is True
    assert body["exercise"]["used_weight"] == 82.5


def test_complete_exercise_already_completed(client, member_token, started_session):
    we_id = started_session["workout_exercise"].id

    # Completa pela primeira vez
    client.put(
        f"/gym_member/complete_exercise/{we_id}",
        json={"used_weight": 80.0},
        headers=auth_header(member_token),
    )

    # Tenta completar novamente
    response = client.put(
        f"/gym_member/complete_exercise/{we_id}",
        json={"used_weight": 80.0},
        headers=auth_header(member_token),
    )
    assert response.status_code == 400
    assert "já foi concluído" in response.json()["detail"]


def test_complete_exercise_not_found(client, member_token, member_user, sample_exercise):
    # Precisa haver uma sessão ativa para que o filtro de status funcione
    # Sem sessão, o exercício não é encontrado
    response = client.put(
        "/gym_member/complete_exercise/99999",
        json={"used_weight": 80.0},
        headers=auth_header(member_token),
    )
    assert response.status_code == 404


def test_complete_exercise_forbidden_after_session_finished(
    client, member_token, started_session
):
    session_id = started_session["session"].id
    we_id = started_session["workout_exercise"].id

    # Finaliza a sessão
    client.put(
        f"/gym_member/finish_workout/{session_id}",
        headers=auth_header(member_token),
    )

    # Tenta completar exercício com sessão já finalizada
    response = client.put(
        f"/gym_member/complete_exercise/{we_id}",
        json={"used_weight": 80.0},
        headers=auth_header(member_token),
    )
    # O filtro exige WorkoutSession.status == started, então retorna 404
    assert response.status_code == 404


def test_complete_exercise_forbidden_trainer(client, trainer_token, started_session):
    we_id = started_session["workout_exercise"].id
    response = client.put(
        f"/gym_member/complete_exercise/{we_id}",
        json={"used_weight": 80.0},
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 403


def test_complete_exercise_unauthenticated(client, started_session):
    we_id = started_session["workout_exercise"].id
    response = client.put(
        f"/gym_member/complete_exercise/{we_id}",
        json={"used_weight": 80.0},
    )
    assert response.status_code == 401
