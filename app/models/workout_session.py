import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime, UTC

class SessionStatus(str, enum.Enum):
    started = "começou"
    finished = "finalizou"
    expired = "exripou"


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    workout_type = Column(String, nullable=False)

    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False )
    finished_at = Column(DateTime(timezone=True), nullable=True)

    status = Column(
        Enum(SessionStatus),
        default=SessionStatus.started,
        nullable=False
    )

    user = relationship("User", back_populates="workout_sessions")