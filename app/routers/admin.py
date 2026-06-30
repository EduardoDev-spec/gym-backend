from typing import Annotated, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Path
from ..models.users import User, UserRole
from ..models.exercises import Exercises
from ..database import SessionLocal
from .auth import get_current_user
from passlib.context import CryptContext
from  ..schemas.admin import UserResponse, CreateExerciseRequest
from ..schemas.auth import CreateUserRequest



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
  
@router.post('/create_user', status_code=status.HTTP_201_CREATED)
async def create_user(user: user_dependency, db: db_dependency, create_user_request: CreateUserRequest):
    if user.get('role') != UserRole.admin:
        raise HTTPException(status_code=403, detail="Acesso negado. Área exclusiva para administradores.")
    
    existing_user = db.query(User).filter(User.email == create_user_request.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail='Email já cadastrado')

    create_trainer_model = User(
        name = create_user_request.name,
        email = create_user_request.email,
        hashed_password = bcrypt_context.hash(create_user_request.password),
        role = UserRole.trainer,
        phone_number = create_user_request.phone_number,
    )

    db.add(create_trainer_model)
    db.commit()
    return {'message': f'Treinador {create_trainer_model.name} criado com sucesso'}

@router.put('/gym_member/{user_id}/edit_exercises/{exercise_id}')
async def edit_exercises(user: user_dependency, db: db_dependency, user_id: int, exercise_id: int, exercises_request: CreateExerciseRequest):
    if user.get('role') != UserRole.admin:
        raise HTTPException(status_code=404, detail="Acesso negado. Área exclusiva para treinadores.")
    
    exercise  = db.query(Exercises).filter(Exercises.id == exercise_id, Exercises.user_id == user_id).first()
    if not exercise :
        raise HTTPException(status_code=404, detail='Não foi possivel encontrar essa busca. Verifique se o ID existe e pertence a um aluno e ou o exercicio.')

    
    exercise.name_exercises = exercises_request.name_exercises
    exercise.workout_type = exercises_request.workout_type
    exercise.sets = exercises_request.sets
    exercise.reps = exercises_request.reps
    exercise.weight = exercises_request.weight
        
    db.commit()
    db.refresh(exercise)

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