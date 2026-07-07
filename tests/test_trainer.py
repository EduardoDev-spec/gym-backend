"""
Testes para o router /trainer:
  GET    /trainer/read_gym_members
  GET    /trainer/read_gym_members/{user_id}
  POST   /trainer/gym_member/{user_id}/exercises
  PUT    /trainer/gym_member/{user_id}/edit_exercises/{exercise_id}
  DELETE /trainer/gym_member/{user_id}/exercises/{exercise_id}
  DELETE /trainer/gym_member/{user_id}/workout/{workout_type}
  POST   /trainer/gym_member/{user_id}/physical_assessment
  GET    /trainer/gym_member/physical_assessment/{user_id}
"""

from tests.conftest import auth_header


# ── GET /trainer/read_gym_members ─────────────────────────────────────────────

def test_trainer_read_gym_members_success(client, trainer_token, member_user):
    response = client.get("/trainer/read_gym_members", headers=auth_header(trainer_token))
    assert response.status_code == 200
    emails = [u["email"] for u in response.json()]
    assert member_user.email in emails


def test_trainer_read_gym_members_filter_by_name(client, trainer_token, member_user):
    response = client.get(
        f"/trainer/read_gym_members?name={member_user.name[:5]}",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_trainer_read_gym_members_forbidden_admin(client, admin_token):
    response = client.get("/trainer/read_gym_members", headers=auth_header(admin_token))
    assert response.status_code == 403


def test_trainer_read_gym_members_forbidden_member(client, member_token):
    response = client.get("/trainer/read_gym_members", headers=auth_header(member_token))
    assert response.status_code == 403


def test_trainer_read_gym_members_unauthenticated(client):
    response = client.get("/trainer/read_gym_members")
    assert response.status_code == 401


# ── GET /trainer/read_gym_members/{user_id} ───────────────────────────────────

def test_trainer_read_gym_member_by_id_success(client, trainer_token, member_user):
    response = client.get(
        f"/trainer/read_gym_members/{member_user.id}",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 200
    assert response.json()["email"] == member_user.email


def test_trainer_read_gym_member_by_id_not_found(client, trainer_token):
    response = client.get(
        "/trainer/read_gym_members/99999",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 404


def test_trainer_read_gym_member_by_id_returns_404_for_trainer(
    client, trainer_token, trainer_user
):
    # Outro treinador não deve aparecer na rota de alunos
    response = client.get(
        f"/trainer/read_gym_members/{trainer_user.id}",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 404


def test_trainer_read_gym_member_by_id_forbidden(client, admin_token, member_user):
    response = client.get(
        f"/trainer/read_gym_members/{member_user.id}",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 403


# ── PUT /trainer/gym_member/{user_id}/edit_exercises/{exercise_id} ─────────────

def test_trainer_edit_exercise_success(client, trainer_token, member_user, sample_exercise):
    payload = {
        "name_exercises": "Supino Inclinado",
        "workout_type": "B",
        "sets": 4,
        "reps": 8,
        "weight": "70kg",
    }
    response = client.put(
        f"/trainer/gym_member/{member_user.id}/edit_exercises/{sample_exercise.id}",
        json=payload,
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 200


def test_trainer_edit_exercise_not_found(client, trainer_token, member_user):
    payload = {
        "name_exercises": "X",
        "workout_type": "B",
        "sets": 1,
        "reps": 1,
        "weight": None,
    }
    response = client.put(
        f"/trainer/gym_member/{member_user.id}/edit_exercises/99999",
        json=payload,
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 404


def test_trainer_edit_exercise_forbidden(client, admin_token, member_user, sample_exercise):
    payload = {
        "name_exercises": "X",
        "workout_type": "B",
        "sets": 1,
        "reps": 1,
        "weight": None,
    }
    response = client.put(
        f"/trainer/gym_member/{member_user.id}/edit_exercises/{sample_exercise.id}",
        json=payload,
        headers=auth_header(admin_token),
    )
    assert response.status_code == 403


# ── DELETE /trainer/gym_member/{user_id}/exercises/{exercise_id} ──────────────

def test_trainer_delete_exercise_success(client, trainer_token, member_user, sample_exercise, db):
    from app.models.exercises import Exercises

    response = client.delete(
        f"/trainer/gym_member/{member_user.id}/exercises/{sample_exercise.id}",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 200

    deleted = db.query(Exercises).filter(Exercises.id == sample_exercise.id).first()
    assert deleted is None


def test_trainer_delete_exercise_not_found(client, trainer_token, member_user):
    response = client.delete(
        f"/trainer/gym_member/{member_user.id}/exercises/99999",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 404


def test_trainer_delete_exercise_forbidden(client, admin_token, member_user, sample_exercise):
    response = client.delete(
        f"/trainer/gym_member/{member_user.id}/exercises/{sample_exercise.id}",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 403


# ── DELETE /trainer/gym_member/{user_id}/workout/{workout_type} ───────────────

def test_trainer_delete_workout_success(client, trainer_token, member_user, sample_exercise, db):
    from app.models.exercises import Exercises

    response = client.delete(
        f"/trainer/gym_member/{member_user.id}/workout/A",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 200

    remaining = (
        db.query(Exercises)
        .filter(Exercises.user_id == member_user.id, Exercises.workout_type == "A")
        .all()
    )
    assert remaining == []


def test_trainer_delete_workout_not_found(client, trainer_token, member_user):
    response = client.delete(
        f"/trainer/gym_member/{member_user.id}/workout/Z",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 404


# ── POST /trainer/gym_member/{user_id}/physical_assessment ───────────────────

ASSESSMENT_PAYLOAD = {
    "weight": 80.0,
    "height": 175.0,
    "body_fat": 15.0,
    "neck": 38.0,
    "chest": 100.0,
    "waist": 80.0,
    "abdomen": 85.0,
    "hips": 95.0,
    "right_arm": 35.0,
    "left_arm": 34.5,
    "right_forearm": 28.0,
    "left_forearm": 27.5,
    "right_thigh": 58.0,
    "left_thigh": 57.5,
    "right_calf": 37.0,
    "left_calf": 36.5,
    "blood_pressure": "120/80",
    "heart_rate": 65,
    "observations": "Bom condicionamento físico.",
}


def test_physical_assessment_success(client, trainer_token, member_user):
    response = client.post(
        f"/trainer/gym_member/{member_user.id}/physical_assessment",
        json=ASSESSMENT_PAYLOAD,
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["users_id"] == member_user.id
    assert body["weight"] == 80.0
    assert body["height"] == 175.0


def test_physical_assessment_bmi_calculation(client, trainer_token, member_user):
    # weight=80, height=175 → IMC = 80 / (1.75²) = 26.12
    response = client.post(
        f"/trainer/gym_member/{member_user.id}/physical_assessment",
        json=ASSESSMENT_PAYLOAD,
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 201
    bmi = response.json()["bmi"]
    assert abs(bmi - 26.12) < 0.1


def test_physical_assessment_fat_and_lean_mass(client, trainer_token, member_user):
    # body_fat=15% de 80kg → fat_mass=12, lean_mass=68
    response = client.post(
        f"/trainer/gym_member/{member_user.id}/physical_assessment",
        json=ASSESSMENT_PAYLOAD,
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 201
    body = response.json()
    assert abs(body["fat_mass"] - 12.0) < 0.1
    assert abs(body["lean_mass"] - 68.0) < 0.1


def test_physical_assessment_without_body_fat(client, trainer_token, member_user):
    # Sem body_fat → fat_mass e lean_mass devem ser None
    payload = {"weight": 75.0, "height": 170.0}
    response = client.post(
        f"/trainer/gym_member/{member_user.id}/physical_assessment",
        json=payload,
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["fat_mass"] is None
    assert body["lean_mass"] is None


def test_physical_assessment_member_not_found(client, trainer_token):
    response = client.post(
        "/trainer/gym_member/99999/physical_assessment",
        json=ASSESSMENT_PAYLOAD,
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 404


def test_physical_assessment_forbidden_admin(client, admin_token, member_user):
    response = client.post(
        f"/trainer/gym_member/{member_user.id}/physical_assessment",
        json=ASSESSMENT_PAYLOAD,
        headers=auth_header(admin_token),
    )
    assert response.status_code == 403


def test_physical_assessment_forbidden_member(client, member_token, member_user):
    response = client.post(
        f"/trainer/gym_member/{member_user.id}/physical_assessment",
        json=ASSESSMENT_PAYLOAD,
        headers=auth_header(member_token),
    )
    assert response.status_code == 403


# ── GET /trainer/gym_member/physical_assessment/{user_id} ─────────────────────

def test_trainer_get_physical_assessment_success(client, trainer_token, member_user):
    client.post(
        f"/trainer/gym_member/{member_user.id}/physical_assessment",
        json=ASSESSMENT_PAYLOAD,
        headers=auth_header(trainer_token),
    )

    response = client.get(
        f"/trainer/gym_member/physical_assessment/{member_user.id}",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["users_id"] == member_user.id
    assert body["weight"] == 80.0


def test_trainer_get_physical_assessment_member_not_found(client, trainer_token):
    response = client.get(
        "/trainer/gym_member/physical_assessment/99999",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 404
    assert "não existe" in response.json()["detail"]


def test_trainer_get_physical_assessment_not_created_yet(client, trainer_token, member_user):
    response = client.get(
        f"/trainer/gym_member/physical_assessment/{member_user.id}",
        headers=auth_header(trainer_token),
    )
    assert response.status_code == 404
    assert "não tem avaliação" in response.json()["detail"]


def test_trainer_get_physical_assessment_forbidden_admin(client, admin_token, member_user):
    response = client.get(
        f"/trainer/gym_member/physical_assessment/{member_user.id}",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 403


def test_trainer_get_physical_assessment_forbidden_member(client, member_token, member_user):
    response = client.get(
        f"/trainer/gym_member/physical_assessment/{member_user.id}",
        headers=auth_header(member_token),
    )
    assert response.status_code == 403


def test_trainer_get_physical_assessment_unauthenticated(client, member_user):
    response = client.get(f"/trainer/gym_member/physical_assessment/{member_user.id}")
    assert response.status_code == 401
