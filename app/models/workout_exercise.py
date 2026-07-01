from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from ..database import Base

class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id = Column(Integer, primary_key=True)

    workout_session_id = Column(
        Integer,
        ForeignKey("workout_sessions.id"),
        nullable=False
    )

    exercise_id = Column(
        Integer,
        ForeignKey("exercises.id"),
        nullable=False
    )

    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    used_weight = Column(Float, nullable=True)

    session = relationship("WorkoutSession")
    exercise = relationship("Exercises")