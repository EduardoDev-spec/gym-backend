from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    phone_number: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class CreateExerciseRequest(BaseModel):
    name_exercises: str
    workout_type: str
    sets: int
    reps: int
    weight: Optional[str] = None
    
    class Config:
        from_attributes = True
