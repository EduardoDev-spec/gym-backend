from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from app.models.users import UserRole

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole = UserRole.aluno

class UserCreate(UserBase):
    password = str

class UserResponse(BaseModel):
    id: int
    is_active: bool
    create_at: datetime

    model_config = ConfigDict(from_attributes=True)