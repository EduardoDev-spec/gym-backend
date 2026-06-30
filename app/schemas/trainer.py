from pydantic import BaseModel
from typing import Optional

class PhysicalAssessmentRequest(BaseModel):
    
    weight: float
    height: float

    body_fat: Optional[float] = None

    neck: Optional[float] = None
    chest: Optional[float] = None
    waist: Optional[float] = None
    abdomen: Optional[float] = None
    hips: Optional[float] = None

    right_arm: Optional[float] = None
    left_arm: Optional[float] = None

    right_forearm: Optional[float] = None
    left_forearm: Optional[float] = None

    right_thigh: Optional[float] = None
    left_thigh: Optional[float] = None

    right_calf: Optional[float] = None
    left_calf: Optional[float] = None

    blood_pressure: Optional[str] = None
    heart_rate: Optional[int] = None

    observations: Optional[str] = None