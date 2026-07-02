from typing import Annotated, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Path
from ..models.users import User, UserRole
from ..models.exercises import Exercises
from ..models.workout_session import WorkoutSession, SessionStatus
from ..models.workout_exercise import WorkoutExercise
from ..models.physical_assessment import PhysicalAssessment
from ..schemas.trainer import PhysicalAssessmentRequest
from ..schemas.gym_member import CompleteExerciseRequest
from ..database import SessionLocal
from .auth import get_current_user
from passlib.context import CryptContext
from ..schemas.gym_member import StartWorkoutSessionRequest, WorkoutSessionResponse
from datetime import datetime, UTC


router = APIRouter(prefix='/gym_member', tags=['gym_member'] )

def get_db():
    db = SessionLocal()
    try:
        yield db

    finally:
        db.close()

db_dependency =  Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get('/workout/{workout_type}')
async def get_workout(
    user: user_dependency,
    db: db_dependency,
    workout_type: str
):
    if user.get('role') != UserRole.gym_member:
        raise HTTPException(
            status_code=403,
            detail='Acesso negado.'
        )

    exercises = (
        db.query(Exercises)
        .filter(
            Exercises.user_id == user.get("id"),
            Exercises.workout_type == workout_type
        )
        .all()
    )

    if not exercises:
        raise HTTPException(
            status_code=404,
            detail='Nenhum exercício encontrado.'
        )

    return exercises

@router.post(
    "/start_workout",
    response_model=WorkoutSessionResponse,
    status_code=status.HTTP_201_CREATED
)
async def start_workout(
    user: user_dependency,
    db: db_dependency,
    request: StartWorkoutSessionRequest
):
    if user.get("role") != UserRole.gym_member:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado."
        )

   
    exercises = (
        db.query(Exercises)
        .filter(
            Exercises.user_id == user["id"],
            Exercises.workout_type == request.workout_type
        )
        .all()
    )

    if not exercises:
        raise HTTPException(
            status_code=404,
            detail="Treino não encontrado."
        )

    
    session = (
        db.query(WorkoutSession)
        .filter(
            WorkoutSession.user_id == user["id"],
            WorkoutSession.status == SessionStatus.started
        )
        .first()
    )

    if session:
        raise HTTPException(
            status_code=400,
            detail="Você já possui um treino em andamento."
        )

    
    new_session = WorkoutSession(
        user_id=user["id"],
        workout_type=request.workout_type,
        started_at=datetime.now(UTC),
        status=SessionStatus.started
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    for exercise in exercises:

        workout_exercise = WorkoutExercise(
            workout_session_id=new_session.id,
            exercise_id=exercise.id,
            completed=False
        )

        db.add(workout_exercise)

    db.commit()

    return new_session

@router.put('/finish_workout/{session_id}', response_model=WorkoutSessionResponse)
async def finish_workout(
    user: user_dependency,
    db: db_dependency,
    session_id: int
):
    if user.get("role") != UserRole.gym_member:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado."
        )

    session = (
        db.query(WorkoutSession)
        .filter(
            WorkoutSession.id == session_id,
            WorkoutSession.user_id == user["id"]
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Sessão de treino não encontrada."
        )

    if session.status != SessionStatus.started:
        raise HTTPException(
            status_code=400,
            detail="Essa sessão já foi finalizada."
        )

    session.finished_at = datetime.now(UTC)
    session.status = SessionStatus.finished

    db.commit()
    db.refresh(session)

    return session

@router.put("/complete_exercise/{workout_exercise_id}")
async def complete_exercise(
    workout_exercise_id: int,
    request: CompleteExerciseRequest,
    user: user_dependency,
    db: db_dependency
):
    if user.get("role") != UserRole.gym_member:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado."
        )

    workout_exercise = (
        db.query(WorkoutExercise)
        .join(WorkoutSession)
        .filter(
            WorkoutExercise.id == workout_exercise_id,
            WorkoutSession.user_id == user["id"],
            WorkoutSession.status == SessionStatus.started
        )
        .first()
    )

    if not workout_exercise:
        raise HTTPException(
            status_code=404,
            detail="Exercício não encontrado ou não pertence ao treino em andamento."
        )

    if workout_exercise.completed:
        raise HTTPException(
            status_code=400,
            detail="Esse exercício já foi concluído."
        )

    workout_exercise.completed = True
    workout_exercise.completed_at = datetime.now(UTC)

    workout_exercise.used_weight = request.used_weight


    db.commit()
    db.refresh(workout_exercise)

    return {
        "message": "Exercício concluído com sucesso.",
        "exercise": workout_exercise
    }

@router.get('/gym_member/physical_assessment', response_model=PhysicalAssessmentRequest)
async def get_physical_assessment(user: user_dependency, db:db_dependency):
    if user.get('role') != UserRole.gym_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado."
        )
    
    physical_assessment = db.query(PhysicalAssessment).filter(PhysicalAssessment.users_id == user.get('id')).first()

    if not physical_assessment:
        raise HTTPException(status_code=404, detail='Você não possui avaliação fisica ainda, agende com nossos funcionarios!')
    
    return physical_assessment
    