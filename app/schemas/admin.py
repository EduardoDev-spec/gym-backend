import re
from pydantic import BaseModel, field_validator, EmailStr
from datetime import datetime
from typing import Optional
from validate_docbr import CPF

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    cpf: str
    phone_number: str
    address: str
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
