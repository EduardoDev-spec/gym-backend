from pydantic import BaseModel
from app.models.users import UserRole

class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    role: UserRole
    phone_number: str

class Token(BaseModel):
    access_token: str
    token_type: str