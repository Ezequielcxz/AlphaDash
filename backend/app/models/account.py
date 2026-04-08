"""Account model for MT5 trading accounts."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class AccountType(str, enum.Enum):
    """Account type enumeration."""
    REAL = "Real"
    DEMO = "Demo"
    PROP = "Prop"


class Account(Base):
    """MT5 trading account model."""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(Integer, unique=True, nullable=False, index=True)
    broker_name = Column(String(100), nullable=True)
    account_type = Column(
        SQLEnum(AccountType),
        default=AccountType.DEMO,
        nullable=False
    )
    alias_personalizado = Column(String(100), nullable=True)
    balance_inicial = Column(Float, default=0.0)
    credito = Column(Float, default=0.0)
    current_balance = Column(Float, default=0.0)
    current_equity = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship to trades
    trades = relationship("Trade", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Account {self.account_number} - {self.broker_name}>"