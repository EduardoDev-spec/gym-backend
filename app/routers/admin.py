from typing import Annotated, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Path
from ..models.users import User, UserRole
from ..models.exercises import Exercises
from ..database import SessionLocal
from .auth import get_current_user
from passlib.context import CryptContext
from  ..schemas.admin import UserResponse, CreateExerciseRequest



router = APIRouter(prefix='/admin', tags=['admin'] )

def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()

db_dependency =  Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

@router.get('/read_gym_members', response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_gym_member(user: user_dependency, db: db_dependency, name: Optional[str] = None, limit: int = 20, skip: int = 0 ):

    if user.get("role") != UserRole.admin:
        raise HTTPException(
        status_code=403,
        detail="Acesso negado. Área exclusiva para administradores."
    )
    query = db.query(User).filter(User.role == UserRole.gym_member)
    if name:
        query = query.filter(User.name.ilike(f'%{name}%'))

    user_model = query.offset(skip).limit(limit).all()
    return user_model   


@router.get('/read_trainers', response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_trainer(user: user_dependency, db: db_dependency, name: Optional[str] = None, limit: int = 20, skip: int = 0 ):
    if user.get("role") != UserRole.admin:
        raise HTTPException(
        status_code=403,
        detail="Acesso negado. Área exclusiva para administradores."
    )
    query = db.query(User).filter(User.role == UserRole.trainer)
    if name:
        query = query.filter(User.name.ilike(f'%{name}%'))

    user_model = query.offset(skip).limit(limit).all()
    return user_model
  
@router.get('/gym_member/{user_id}', response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_gym_member_by_id(user_id: int, user: user_dependency, db:db_dependency):
    if user.get('role') != UserRole.admin:
        raise HTTPException(status_code=403, detail="Acesso negado. Área exclusiva para administradores.")
    
    user_model = db.query(User).filter(User.id == user_id, User.role == UserRole.gym_member).first()

    if not user_model:
        raise HTTPException(status_code=404, detail='Aluno não encontrado. Verifique se o ID existe e pertence a um aluno.')
    
    return user_model


@router.get('/trainer/{user_id}', response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_trainer_by_id(user_id: int, user: user_dependency, db:db_dependency):
    if user.get('role') != UserRole.admin:
        raise HTTPException(status_code=403, detail="Acesso negado. Área exclusiva para administradores.")
    
    user_model = db.query(User).filter(User.id == user_id, User.role == UserRole.trainer).first()
    
    if not user_model:
        raise HTTPException(status_code=404, detail='Aluno não encontrado. Verifique se o ID existe e pertence a um aluno.')
    
    return user_model

@router.get('/gym_member/{user_id}/toggle_status', status_code=status.HTTP_200_OK)
async def get_trainer_by_id(user_id: int, user: user_dependency, db:db_dependency):
    if user.get('role') != UserRole.admin:
        raise HTTPException(status_code=403, detail="Acesso negado. Área exclusiva para administradores.")
    
    user_model = db.query(User).filter(User.id == user_id, User.role == UserRole.gym_member).first()
    
    if not user_model:
        raise HTTPException(status_code=404, detail='Aluno não encontrado. Verifique se o ID existe e pertence a um aluno.')
    
    user_model.is_active = not user_model.is_active
    db.add(user_model)
    db.commit()

    current_status = 'Ativo' if user_model.is_active else "Bloqueado"
    return {"message": f"Status do aluno atualizado para: {current_status}"}

@router.post('/gym_member/{user_id}/exercises', status_code=status.HTTP_200_OK)
async def create_exercises_for_gym_member(user_id: int, exercises_request: list[CreateExerciseRequest], user: user_dependency, db:db_dependency):
    if user.get('role') != UserRole.admin:
        raise HTTPException(status_code=403, detail="Acesso negado. Área exclusiva para administradores.")
    
    gym_member = db.query(User).filter(User.id == user_id, User.role == UserRole.gym_member).first()

    if not gym_member:
        raise HTTPException(status_code=404, detail='Aluno não encontrado. Não é possível associar um exercício.')
    
    lista_exercicios_db = []
    
    for exercise in exercises_request:
        new_exercise = Exercises(
            name_exercises = exercise.name_exercises,
            workout_type = exercise.workout_type,
            sets = exercise.sets,
            reps = exercise.reps,
            weight = exercise.weight,
            user_id = user_id
        )
        lista_exercicios_db.append(new_exercise)

    db.add_all(lista_exercicios_db)
    db.commit()

    return {
        "message": f"{len(lista_exercicios_db)} exercícios cadastrados com sucesso para o aluno {gym_member.name}."
    }