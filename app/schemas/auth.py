import re
from pydantic import BaseModel, EmailStr, field_validator
from app.models.users import UserRole
from validate_docbr import CPF

cpf_validator = CPF()


class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    cpf: str
    password: str
    role: UserRole
    address: str
    phone_number: str


    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, value: str):
        cpf = re.sub(r'\D', '', value)

        if len(cpf) != 11:
            raise ValueError("CPF deve conter 11 dígitos")

        if not cpf_validator.validate(cpf):
            raise ValueError("CPF inválido")

        return cpf

class Token(BaseModel):
    access_token: str
    token_type: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str