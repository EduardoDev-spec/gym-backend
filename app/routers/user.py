from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Path
from ..models.users import User
from ..database import SessionLocal
from .auth import get_current_user
from passlib.context import CryptContext


router = APIRouter(prefix='/user', tags=['user'] )

def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()

db_dependency =  Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

@router.get('/me', status_code=status.HTTP_200_OK)
async def get_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail='Você não esta logado')
    user_model = db.query(User).filter(User.id == user.get('id')).first()
    if not user_model:
        raise HTTPException(status_code=404, detail='Não encontrado')
    return user_model