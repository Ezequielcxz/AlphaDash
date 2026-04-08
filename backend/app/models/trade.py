"""Trade model for MT5 trade history."""
from sqlalchemy import Column, Integer, BigInteger, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class TradeType(str, enum.Enum):
    """Trade type enumeration."""
    BUY = "Buy"
    SELL = "Sell"


class Trade(Base):
    """MT5 trade history model."""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    ticket_id = Column(BigInteger, unique=True, nullable=False, index=True)
    magic_number = Column(Integer, nullable=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    type = Column(SQLEnum(TradeType), nullable=False)
    lots = Column(Float, nullable=False)
    open_time = Column(DateTime, nullable=False, index=True)
    close_time = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    sl = Column(Float, nullable=True)
    tp = Column(Float, nullable=True)
    profit_usd = Column(Float, nullable=False)
    pips = Column(Float, nullable=True)
    commission = Column(Float, default=0.0)
    swap = Column(Float, default=0.0)
    mae = Column(Float, nullable=True)  # Maximum Adverse Excursion
    mfe = Column(Float, nullable=True)  # Maximum Favorable Excursion
    created_at = Column(DateTime, server_default=func.now())

    # Relationship to account
    account = relationship("Account", back_populates="trades")

    def __repr__(self):
        return f"<Trade {self.ticket_id} - {self.symbol} {self.type.value}>"

    @property
    def duration_seconds(self):
        """Calculate trade duration in seconds."""
        if self.open_time and self.close_time:
            return (self.close_time - self.open_time).total_seconds()
        return None

    @property
    def is_winner(self):
        """Check if trade is profitable."""
        return self.profit_usd > 0