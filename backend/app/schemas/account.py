"""Account Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AccountType(str, Enum):
    """Account type enumeration."""
    REAL = "Real"
    DEMO = "Demo"
    PROP = "Prop"


class AccountBase(BaseModel):
    """Base account schema."""
    account_number: int = Field(..., description="MT5 account number")
    broker_name: Optional[str] = Field(None, description="Broker name")
    account_type: AccountType = Field(AccountType.DEMO, description="Account type")
    alias_personalizado: Optional[str] = Field(None, description="Custom alias for the account")
    balance_inicial: Optional[float] = Field(0.0, description="Initial balance")
    credito: Optional[float] = Field(0.0, description="Account credit")
    current_balance: Optional[float] = Field(0.0, description="Current balance")
    current_equity: Optional[float] = Field(0.0, description="Current equity")


class AccountCreate(AccountBase):
    """Schema for creating a new account."""
    pass


class AccountUpdate(BaseModel):
    """Schema for updating an account."""
    broker_name: Optional[str] = None
    account_type: Optional[AccountType] = None
    alias_personalizado: Optional[str] = None
    balance_inicial: Optional[float] = None
    credito: Optional[float] = None
    current_balance: Optional[float] = None
    current_equity: Optional[float] = None


class AccountResponse(AccountBase):
    """Schema for account response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True