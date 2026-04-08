"""
Trades Router for AlphaDash.

Handles trade history queries and filtering.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import Trade, Account
from app.schemas.trade import TradeResponse

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("/", response_model=List[TradeResponse])
async def list_trades(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    magic_number: Optional[int] = Query(None, description="Filter by magic number"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_date: Optional[datetime] = Query(None, description="Filter trades from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter trades until this date"),
    result_filter: Optional[str] = Query(None, description="Filter by result: win, loss, all"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db)
):
    """
    List trades with optional filtering.

    Supports filtering by:
    - account_id: Specific account
    - magic_number: Strategy filter
    - symbol: Trading instrument
    - start_date / end_date: Date range
    - result_filter: win, loss, or all
    """
    query = select(Trade)

    # Apply filters
    conditions = []

    if account_id:
        conditions.append(Trade.account_id == account_id)

    if magic_number is not None:
        conditions.append(Trade.magic_number == magic_number)

    if symbol:
        conditions.append(Trade.symbol == symbol.upper())

    if start_date:
        conditions.append(Trade.close_time >= start_date)

    if end_date:
        conditions.append(Trade.close_time <= end_date)

    if result_filter:
        if result_filter.lower() == "win":
            conditions.append(Trade.profit_usd > 0)
        elif result_filter.lower() == "loss":
            conditions.append(Trade.profit_usd < 0)

    if conditions:
        query = query.where(and_(*conditions))

    # Order by close time descending
    query = query.order_by(Trade.close_time.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    trades = result.scalars().all()

    return trades


@router.get("/account/{account_number}", response_model=List[TradeResponse])
async def get_trades_by_account_number(
    account_number: int,
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get trades by account number."""
    # First find account
    result = await db.execute(
        select(Account).where(Account.account_number == account_number)
    )
    account = result.scalar_one_or_none()

    if not account:
        return []

    # Get trades
    result = await db.execute(
        select(Trade)
        .where(Trade.account_id == account.id)
        .order_by(Trade.close_time.desc())
        .limit(limit)
    )
    trades = result.scalars().all()

    return trades


@router.get("/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific trade by ID."""
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    return trade


@router.get("/symbols/list")
async def list_symbols(account_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Get list of all traded symbols."""
    query = select(Trade.symbol).distinct()

    if account_id:
        query = query.where(Trade.account_id == account_id)

    result = await db.execute(query)
    symbols = [row[0] for row in result.all()]

    return {"symbols": sorted(symbols)}


@router.get("/magic-numbers/list")
async def list_magic_numbers(
    account_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get list of all magic numbers (strategies) used."""
    query = select(Trade.magic_number).distinct().where(Trade.magic_number.isnot(None))

    if account_id:
        query = query.where(Trade.account_id == account_id)

    result = await db.execute(query)
    magic_numbers = [row[0] for row in result.all() if row[0] is not None]

    return {"magic_numbers": sorted(magic_numbers)}