"""Trade Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TradeType(str, Enum):
    """Trade type enumeration."""
    BUY = "Buy"
    SELL = "Sell"


class TradeBase(BaseModel):
    """Base trade schema."""
    ticket_id: int = Field(..., description="MT5 ticket ID")
    account_number: int = Field(..., description="MT5 account number")
    magic_number: Optional[int] = Field(None, description="Magic number for strategy identification")
    symbol: str = Field(..., description="Trading symbol")
    type: TradeType = Field(..., description="Trade type (Buy/Sell)")
    lots: float = Field(..., gt=0, description="Lot size")
    open_time: datetime = Field(..., description="Trade open time")
    close_time: datetime = Field(..., description="Trade close time")
    open_price: float = Field(..., description="Entry price")
    close_price: float = Field(..., description="Exit price")
    sl: Optional[float] = Field(None, description="Stop loss price")
    tp: Optional[float] = Field(None, description="Take profit price")
    profit_usd: float = Field(..., description="Profit in USD")
    pips: Optional[float] = Field(None, description="Profit in pips")
    commission: Optional[float] = Field(0.0, description="Commission")
    swap: Optional[float] = Field(0.0, description="Swap")
    mae: Optional[float] = Field(None, description="Maximum Adverse Excursion")
    mfe: Optional[float] = Field(None, description="Maximum Favorable Excursion")


class TradeCreate(TradeBase):
    """Schema for creating a new trade."""
    pass


class TradeResponse(BaseModel):
    """Schema for trade response."""
    id: int
    account_id: int
    ticket_id: int
    magic_number: Optional[int]
    symbol: str
    type: TradeType
    lots: float
    open_time: datetime
    close_time: datetime
    open_price: float
    close_price: float
    sl: Optional[float]
    tp: Optional[float]
    profit_usd: float
    pips: Optional[float]
    commission: float
    swap: float
    mae: Optional[float]
    mfe: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class TradeUpload(BaseModel):
    """Schema for CSV upload batch."""
    account_number: int
    broker_name: Optional[str] = None
    account_type: str = "Demo"
    trades: list[TradeBase]