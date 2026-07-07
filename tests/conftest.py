import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from passlib.context import CryptContext
from datetime import timedelta

from app.main import app
from app.database import Base
from app.models.users import User, UserRole
from app.models.exercises import Exercises
from app.models.workout_session import WorkoutSession, SessionStatus
from app.models.workout_exercise import WorkoutExercise
from app.routers.auth import get_db as auth_get_db, create_access_token
from app.routers.user import get_db as user_get_db
from app.routers.admin import get_db as admin_get_db
from app.routers.trainer import get_db as trainer_get_db
from app.routers.gym_member import get_db as gym_member_get_db
from app.models.plans import Plan
from app.models.subscriptions import Subscription, SubscriptionStatus
from app.services.mercado_pago import mercado_pago_service

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[auth_get_db] = override_get_db
    app.dependency_overrides[user_get_db] = override_get_db
    app.dependency_overrides[admin_get_db] = override_get_db
    app.dependency_overrides[trainer_get_db] = override_get_db
    app.dependency_overrides[gym_member_get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def make_token(user_id: int, email: str, role: str) -> str:
    return create_access_token(email, user_id, role, timedelta(minutes=30))


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── User fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture()
def admin_user(db):
    user = User(
        name="Admin Teste",
        email="admin@test.com",
        cpf="86454404820",
        hashed_password=bcrypt_context.hash("Admin123!"),
        role=UserRole.admin,
        address="Rua Admin, 100",
        phone_number="11999999999",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def trainer_user(db):
    user = User(
        name="Treinador Teste",
        email="trainer@test.com",
        cpf="87393124378",
        hashed_password=bcrypt_context.hash("Trainer123!"),
        role=UserRole.trainer,
        address="Rua Treinador, 200",
        phone_number="11988888888",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def member_user(db):
    user = User(
        name="Aluno Teste",
        email="member@test.com",
        cpf="93393084844",
        hashed_password=bcrypt_context.hash("Member123!"),
        role=UserRole.gym_member,
        address="Rua Aluno, 300",
        phone_number="11977777777",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def inactive_member(db):
    user = User(
        name="Aluno Inativo",
        email="inactive@test.com",
        cpf="51483682846",
        hashed_password=bcrypt_context.hash("Inactive123!"),
        role=UserRole.gym_member,
        address="Rua Inativo, 400",
        phone_number="11966666666",
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Token fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture()
def admin_token(admin_user):
    return make_token(admin_user.id, admin_user.email, admin_user.role)


@pytest.fixture()
def trainer_token(trainer_user):
    return make_token(trainer_user.id, trainer_user.email, trainer_user.role)


@pytest.fixture()
def member_token(member_user):
    return make_token(member_user.id, member_user.email, member_user.role)


# ── Exercise / Session fixtures ────────────────────────────────────────────────

@pytest.fixture()
def sample_exercise(db, member_user):
    exercise = Exercises(
        name_exercises="Supino Reto",
        workout_type="A",
        sets=3,
        reps=10,
        weight="80kg",
        user_id=member_user.id,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


@pytest.fixture()
def started_session(db, member_user, sample_exercise):
    session = WorkoutSession(
        user_id=member_user.id,
        workout_type="A",
        status=SessionStatus.started,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    we = WorkoutExercise(
        workout_session_id=session.id,
        exercise_id=sample_exercise.id,
        completed=False,
    )
    db.add(we)
    db.commit()
    db.refresh(we)

    return {"session": session, "workout_exercise": we}


# ── Mercado Pago mock ────────────────────────────────────────────────────────
# Nunca chama a API real do Mercado Pago nos testes: substitui os métodos do
# serviço por dublês que devolvem respostas de sucesso previsíveis.

@pytest.fixture()
def mock_mercado_pago(monkeypatch):
    monkeypatch.setattr(
        mercado_pago_service,
        "create_plan",
        lambda name, price, duration_days: {"id": "mp-plan-123"},
    )
    monkeypatch.setattr(
        mercado_pago_service,
        "create_subscription",
        lambda plan_id, payer_email: {
            "id": "mp-subscription-123",
            "init_point": "https://mercadopago.com/checkout/mp-subscription-123",
        },
    )


# ── Plan / Subscription fixtures ────────────────────────────────────────────

@pytest.fixture()
def sample_plan(db):
    plan = Plan(
        name="Plano Mensal",
        description="Acesso completo por 30 dias",
        price=99.9,
        duration_days=30,
        active=True,
        mercado_pago_plan_id="mp-plan-existing",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@pytest.fixture()
def inactive_plan(db):
    plan = Plan(
        name="Plano Descontinuado",
        description="Não vendido mais",
        price=49.9,
        duration_days=30,
        active=False,
        mercado_pago_plan_id="mp-plan-inactive",
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@pytest.fixture()
def pending_subscription(db, member_user, sample_plan):
    subscription = Subscription(
        user_id=member_user.id,
        plan_id=sample_plan.id,
        status=SubscriptionStatus.pending,
        mercado_pago_subscription_id="mp-subscription-existing",
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription
