from datetime import datetime
from pydantic import BaseModel, ConfigDict

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CreatePlanRequest(BaseModel):
    name: str
    description: str | None = None
    price: float
    duration_days: int


class UpdatePlanRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    duration_days: int | None = None
    active: bool | None = None


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    mercado_pago_plan_id: str | None

    id: int
    name: str
    description: str | None
    price: float
    duration_days: int
    active: bool
    created_at: datetime

class PublicPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: float
    duration_days: int