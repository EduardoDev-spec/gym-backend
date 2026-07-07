from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..database import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    description = Column(String, nullable=True)

    price = Column(Float, nullable=False)

    duration_days = Column(Integer, nullable=False)

    active = Column(Boolean, default=True)

    # ID do plano criado no Mercado Pago
    mercado_pago_plan_id = Column(
        String,
        nullable=True,
        unique=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    subscriptions = relationship(
        "Subscription",
        back_populates="plan"
    )