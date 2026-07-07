from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Enum as SqlEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from ..database import Base


class SubscriptionStatus(str, Enum):
    pending = "pending"          # Aguardando pagamento
    approved = "approved"        # Assinatura ativa
    paused = "paused"            # Assinatura pausada
    cancelled = "cancelled"      # Cancelada
    expired = "expired"          # Expirada


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    plan_id = Column(
        Integer,
        ForeignKey("plans.id"),
        nullable=False
    )

    status = Column(
        SqlEnum(SubscriptionStatus),
        default=SubscriptionStatus.pending,
        nullable=False
    )

    # ==========================
    # Mercado Pago
    # ==========================

    mercado_pago_subscription_id = Column(
        String,
        nullable=True
    )

    payment_method = Column(
        String,
        nullable=True
    )

    # ==========================
    # Datas
    # ==========================

    started_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    last_payment_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    next_billing_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # ==========================
    # Relacionamentos
    # ==========================

    user = relationship(
        "User",
        back_populates="subscriptions"
    )

    plan = relationship(
        "Plan",
        back_populates="subscriptions"
    )