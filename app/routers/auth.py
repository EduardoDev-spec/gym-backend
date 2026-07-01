from fastapi import APIRouter, Depends, status, HTTPException, Request
from typing import Annotated
from ..database import SessionLocal
from sqlalchemy.orm import Session
from ..schemas.auth import CreateUserRequest, ChangePasswordRequest
from ..models.users import User
from app.core.config import settings
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone
from jose import jwt, JWTError
from ..schemas.auth import Token, UserRole


router = APIRouter(prefix='/auth', tags=['auth'])

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')




# Utility function (Dependency) to open and close the database session upon request.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

def authenticate_user(email: str, password: str, db):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    if not user.is_active:
        return False
    return user

def create_access_token(email:str, user_id: int, role: str, expires_delta: timedelta):
    encode = {'sub': email, 'id': user_id, 'role': role }
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        user_id: int = payload.get('id')
        role: str = payload.get('role')
        if email is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Não foi possivel validar as credenciais')
        return {'email': email, 'id': user_id, 'role': role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Não foi possivel validar as credenciais')


@router.post('/create_user', status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):

    print(create_user_request.model_dump())   # <-- ADICIONE

    existing_user = db.query(User).filter(
        User.email == create_user_request.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Este e-mail já está em uso."
        )

    create_user_model = User(
        name=create_user_request.name,
        email=create_user_request.email,
        cpf=create_user_request.cpf,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        role=create_user_request.role,
        address=create_user_request.address,
        phone_number=create_user_request.phone_number
    )

    db.add(create_user_model)
    db.commit()


@router.post('/token', response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):

    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Não foi possivel validar as credenciais')
    token = create_access_token(user.email, user.id, user.role, timedelta(minutes=20))

    return {'access_token': token, 'token_type': 'bearer'}

user_dependency = Annotated[dict, Depends(get_current_user)]

@router.put('/change_password', status_code=status.HTTP_200_OK)
async def change_password(user: user_dependency, db: db_dependency, request: ChangePasswordRequest):

    user_model = db.query(User).filter(User.id == user['id']).first()

    if not user_model:
        raise HTTPException(status_code=404, detail='Usuário não encontrado.')
    
    if not bcrypt_context.verify(request.current_password, user_model.hashed_password):
        raise HTTPException(status_code=400, detail='Senha incorreta')
    
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail='As senhas não coincidem.')
    
    if  bcrypt_context.verify(request.new_password, user_model.hashed_password):
        raise HTTPException(status_code=400, detail='A nova senha deve ser diferente da atual.')
    
    user_model.hashed_password = bcrypt_context.hash(request.new_password)

    db.commit()

    return {
        "message": "Senha alterada com sucesso."
    }
    
