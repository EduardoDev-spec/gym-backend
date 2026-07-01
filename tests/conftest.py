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
        hashed_password=bcrypt_context.hash("Admin123!"),
        role=UserRole.admin,
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
        hashed_password=bcrypt_context.hash("Trainer123!"),
        role=UserRole.trainer,
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
        hashed_password=bcrypt_context.hash("Member123!"),
        role=UserRole.gym_member,
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
        hashed_password=bcrypt_context.hash("Inactive123!"),
        role=UserRole.gym_member,
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
