from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime, UTC



class PhysicalAssessment(Base):
    __tablename__ = "physical_assessments"

    id = Column(Integer, primary_key=True, index=True)

    users_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    date = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    weight = Column(Float)
    height = Column(Float)

    bmi = Column(Float)

    body_fat = Column(Float)

    lean_mass = Column(Float)

    fat_mass = Column(Float)

    neck = Column(Float)
    chest = Column(Float)
    waist = Column(Float)
    abdomen = Column(Float)
    hips = Column(Float)

    right_arm = Column(Float)
    left_arm = Column(Float)

    right_forearm = Column(Float)
    left_forearm = Column(Float)

    right_thigh = Column(Float)
    left_thigh = Column(Float)

    right_calf = Column(Float)
    left_calf = Column(Float)

    blood_pressure = Column(String(20))
    heart_rate = Column(Integer)

    observations = Column(String)

    user = relationship("User", back_populates="assessments")