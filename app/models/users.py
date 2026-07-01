import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class UserRole(str, enum.Enum):
    gym_member = 'aluno'
    admin = "admin"
    trainer = 'treinador'


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    cpf = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.gym_member, nullable=False)
    address = Column(String, nullable=False )
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    phone_number = Column(String)

    assessments = relationship(
        "PhysicalAssessment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    workout_sessions = relationship(
        "WorkoutSession",
        back_populates="user"
)