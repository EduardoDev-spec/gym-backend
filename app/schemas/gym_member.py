from enum import Enum
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SessionStatus(str, Enum):
    started = "começou"
    finished = "finalizou"
    expired = "exripou"

class StartWorkoutSessionRequest(BaseModel):
    workout_type: str

class WorkoutSessionResponse(BaseModel):
    id: int
    user_id: int
    workout_type: str
    started_at: datetime
    finished_at: datetime | None = None
    status: SessionStatus

    model_config = ConfigDict(from_attributes=True)


class CompleteExerciseRequest(BaseModel):
    workout_exercise_id: int


class WorkoutExerciseResponse(BaseModel):
    id: int
    workout_session_id: int
    exercise_id: int

    completed: bool
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class CompleteExerciseRequest(BaseModel):
    used_weight: float