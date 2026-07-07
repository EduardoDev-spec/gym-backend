from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.subscriptions import SubscriptionStatus
from ..schemas.plans import PlanResponse

class CreateSubscriptionRequest(BaseModel):
    plan_id: int


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    plan_id: int
    status: SubscriptionStatus
    started_at: datetime | None
    expires_at: datetime | None
    created_at: datetime

class CurrentSubscriptionResponse(BaseModel):
    id: int
    status: SubscriptionStatus
    started_at: datetime | None
    expires_at: datetime | None
    plan: PlanResponse

    payment_method: str | None
    next_billing_at: datetime | None

    last_payment_at: datetime | None
    updated_at: datetime


    model_config = ConfigDict(from_attributes=True)


class AdminSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    student_name: str
    student_email: str

    plan_name: str
    plan_price: float

    status: SubscriptionStatus

    started_at: datetime | None
    expires_at: datetime | None
    created_at: datetime