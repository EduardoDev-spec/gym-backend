from typing import Annotated, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Path
from ..models.users import User, UserRole
from ..models.exercises import Exercises
from ..models.physical_assessment import PhysicalAssessment
from ..database import SessionLocal
from .auth import get_current_user
from  ..schemas.admin import CreateExerciseRequest
from ..schemas.trainer import PhysicalAssessmentRequest

router = APIRouter(prefix='/trainer', tags=['trainer'] )

def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()

db_dependency =  Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/read_gym_members')
async def read_gym_members(user: user_dependency, db: db_dependency, name: Optional[str] = None, limit: int = 20, skip: int = 0):
    if user.get('role') != UserRole.trainer:
        raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acesso negado. Área exclusiva para administradores.")
    
    query = db.query(User).filter(User.role == UserRole.gym_member)
    if name:
        query = query.filter(User.name.ilike(f'%{name}%'))

    user_model = query.offset(skip).limit(limit).all()
    return user_model 

@router.get('/read_gym_members/{user_id}')
async def read_gym_members(user: user_dependency, db: db_dependency, user_id: int):
    if user.get('role') != UserRole.trainer:
        raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acesso negado. Área exclusiva para Treinadores.")
    
    query = db.query(User).filter(User.id == user_id, User.role == UserRole.gym_member).first()
    if not query:
        raise HTTPException(status_code=404, detail='Aluno não encontrado. Verifique se o ID existe e pertence a um aluno.')
    
    return query


@router.post('/gym_member/{user_id}/exercises')
async def create_exercises_for_gym_member(user: user_dependency, db: db_dependency, user_id: int, exercises_request: list[CreateExerciseRequest] ):
    if user.get('role') != UserRole.trainer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Acesso negado. Área exclusiva para Treinadores.')
    
    gym_member = db.query(User.id == user_id, User.role == UserRole.gym_member).first()
    
    if not gym_member:
        raise HTTPException(status_code=404, detail='Aluno não encontrado. Verifique se o ID existe e pertence a um aluno.')

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
    db.commit

    return {
        "message": f"{len(lista_exercicios_db)} exercícios cadastrados com sucesso para o aluno {gym_member.name}."
    }


@router.put('/gym_member/{user_id}/edit_exercises/{exercise_id}')
async def edit_exercises(user: user_dependency, db: db_dependency, user_id: int, exercise_id: int, exercises_request: CreateExerciseRequest):
    if user.get('role') != UserRole.trainer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado. Área exclusiva para treinadores.")
    
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

@router.delete('/gym_member/{user_id}/exercises/{exercise_id}')
async def delete_exercise(user: user_dependency, db: db_dependency, user_id: int, exercise_id: int):
    if user.get('role') != UserRole.trainer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado. Área exclusiva para treinadores.")
    
    exercise  = db.query(Exercises).filter(Exercises.id == exercise_id, Exercises.user_id == user_id).first()

    if not exercise:
        raise HTTPException(
            status_code=404,
            detail="Exercício não encontrado."
        )
    
    db.delete(exercise)
    db.commit()
    return {'mensage': f'Exercicio deletado com sucesso'}



@router.delete('/gym_member/{user_id}/workout/{workout_type}')
async def delete_training(user: user_dependency, db: db_dependency, user_id: int, workout_type: str):
    if user.get('role') != UserRole.trainer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado. Área exclusiva para treinadores.")
    
    exercise  = db.query(Exercises).filter(Exercises.workout_type == workout_type, Exercises.user_id == user_id)

    if not exercise.first():
        raise HTTPException(
            status_code=404,
            detail="Exercício não encontrado."
        )
    
    exercise.delete(synchronize_session=False)
    db.commit()
    return {'mensage': f'Treino excluido com sucesso'}


@router.post(
    "/gym_member/{user_id}/physical_assessment",
    status_code=status.HTTP_201_CREATED
)
async def physical_assessment(
    user: user_dependency,
    db: db_dependency,
    user_id: int,
    physical_assessment: PhysicalAssessmentRequest
):
    # Apenas treinadores podem cadastrar avaliações
    if user.get("role") != UserRole.trainer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Área exclusiva para treinadores."
        )

    # Verifica se o aluno existe
    gym_member = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.role == UserRole.gym_member
        )
        .first()
    )

    if not gym_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado."
        )

    # ============================
    # Cálculos automáticos
    # ============================

    height_m = physical_assessment.height / 100

    bmi = round(
        physical_assessment.weight / (height_m ** 2),
        2
    )

    fat_mass = None
    lean_mass = None

    if physical_assessment.body_fat is not None:
        fat_mass = round(
            physical_assessment.weight *
            (physical_assessment.body_fat / 100),
            2
        )

        lean_mass = round(
            physical_assessment.weight - fat_mass,
            2
        )

    # ============================
    # Criação da avaliação
    # ============================

    form = PhysicalAssessment(

        users_id=user_id,

        weight=physical_assessment.weight,
        height=physical_assessment.height,

        bmi=bmi,

        body_fat=physical_assessment.body_fat,

        lean_mass=lean_mass,
        fat_mass=fat_mass,

        neck=physical_assessment.neck,
        chest=physical_assessment.chest,
        waist=physical_assessment.waist,
        abdomen=physical_assessment.abdomen,
        hips=physical_assessment.hips,

        right_arm=physical_assessment.right_arm,
        left_arm=physical_assessment.left_arm,

        right_forearm=physical_assessment.right_forearm,
        left_forearm=physical_assessment.left_forearm,

        right_thigh=physical_assessment.right_thigh,
        left_thigh=physical_assessment.left_thigh,

        right_calf=physical_assessment.right_calf,
        left_calf=physical_assessment.left_calf,

        blood_pressure=physical_assessment.blood_pressure,
        heart_rate=physical_assessment.heart_rate,

        observations=physical_assessment.observations
    )

    db.add(form)
    db.commit()
    db.refresh(form)

    return form

@router.get('/gym_member/physical_assessment/{user_id}')
async def get_physical_assessment(user: user_dependency, db: db_dependency, user_id: int):
    if user.get('role') != UserRole.trainer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado. Área exclusiva para treinadores.")
    
    gym_member = db.query(User).filter(User.role == UserRole.gym_member, User.id == user_id).first()

    if not gym_member:
        raise HTTPException(status_code=404, detail='Usuario não existe!')
    
    physical_assessment = db.query(PhysicalAssessment).filter(PhysicalAssessment.users_id == user_id).first()

    if not physical_assessment:
        raise HTTPException(status_code=404, detail='O aluno ainda não tem avaliação fisica')

    return physical_assessment