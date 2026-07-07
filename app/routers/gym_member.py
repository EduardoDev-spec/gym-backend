from typing import Annotated, Optional
from sqlalchemy.orm import Session, joinedload
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
from ..schemas.plans import PublicPlanResponse
from ..models.plans import Plan
from ..models.subscriptions import Subscription, SubscriptionStatus
from ..schemas.subscriptions import CreateSubscriptionRequest, CurrentSubscriptionResponse
from ..services.mercado_pago import mercado_pago_service


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


@router.get('/gym_member/workout/current',)
async def current_workout(user: user_dependency, db:db_dependency):
    if user.get('role') != UserRole.gym_member:
        raise HTTPException(status_code=403, detail="Acesso negado.")
    current = db.query(WorkoutSession).filter(WorkoutSession.user_id == user.get('id'), WorkoutSession.status == "started").first()

    if not current:
        raise HTTPException(
            status_code=404,
            detail="Você não tem nenhum treino iniciado!")
    
    workout_exercises = (
        db.query(WorkoutExercise).options(joinedload(WorkoutExercise.exercise)).filter(WorkoutExercise.workout_session_id == current.id).all())
    
   #Alterar mais tarde para um Response deixando mais organizado
    return {
    "session": {
        "id": current.id,
        "workout_type": current.workout_type,
        "started_at": current.started_at,
        "status": current.status,
    },
    "exercises": [
        {
            "id": we.id,
            "name": we.exercise.name_exercises,
            "sets": we.exercise.sets,
            "reps": we.exercise.reps,
            "weight": we.exercise.weight,
            "completed": we.completed,
            "used_weight": we.used_weight,
        }
        for we in workout_exercises
    ]
}



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


@router.get('/plans', response_model=list[PublicPlanResponse], status_code=status.HTTP_200_OK)
async def get_all_plans(user: user_dependency, db:db_dependency):
    if user.get('role') != UserRole.gym_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Área exclusiva para alunos!"
        )
    
    plans = db.query(Plan).filter(Plan.active == True).all()

    return plans

@router.post('/subscriptions')
async def create_subscription(user: user_dependency, db:db_dependency, request: CreateSubscriptionRequest):
    if user.get('role') != UserRole.gym_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Área exclusiva para alunos!"
        )
    plan = db.query(Plan).filter(Plan.id == request.plan_id).first()

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Plano não encontrado."
        )
    
    if not plan.active:
        raise HTTPException(
            status_code=400,
            detail="Este plano não está disponível."
        )
    
    subscription = db.query(Subscription).filter(Subscription.user_id == user.get('id'), Subscription.status.in_(["pending", "approved"])).first()

    if subscription:
        raise HTTPException(
            status_code=400,
            detail="Você já possui uma assinatura ativa ou pendente."
        )
    
    gym_member = db.query(User).filter(User.id == user.get("id")).first()
                  
    mp_subscription = mercado_pago_service.create_subscription(
    plan_id=plan.mercado_pago_plan_id,
    payer_email=gym_member.email)

    new_subscription = Subscription(user_id=user.get("id"),plan_id=plan.id,status=SubscriptionStatus.pending,mercado_pago_subscription_id=mp_subscription["id"])

    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)

    return {"subscription": new_subscription,"checkout_url": mp_subscription["init_point"]}


@router.get(
    "/subscriptions/current",
    response_model=CurrentSubscriptionResponse,
    status_code=status.HTTP_200_OK
)
async def get_current_subscription(
    user: user_dependency,
    db: db_dependency
):
    if user.get("role") != UserRole.gym_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado."
        )

    subscription = (
        db.query(Subscription)
        .filter(Subscription.user_id == user.get("id"))
        .first()
    )

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Você não possui nenhuma assinatura."
        )

    plan = (
        db.query(Plan)
        .filter(Plan.id == subscription.plan_id)
        .first()
    )

    return {
        "id": subscription.id,
        "status": subscription.status,
        "started_at": subscription.started_at,
        "expires_at": subscription.expires_at,
        "plan": plan,
        "payment_method": subscription.payment_method,
        "next_billing_at": subscription.next_billing_at,
        "last_payment_at": subscription.last_payment_at,
        "updated_at": subscription.updated_at,
    }


