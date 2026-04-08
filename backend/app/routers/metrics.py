"""
Metrics Router for AlphaDash.

Handles performance metrics calculations for accounts and portfolio.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Trade, Account
from app.services.metrics_engine import MetricsEngine

router = APIRouter(prefix="/metrics", tags=["metrics"])


async def get_trades_for_metrics(
    db: AsyncSession,
    account_id: Optional[int] = None,
    days: Optional[int] = None
) -> list[dict]:
    """
    Fetch trades from database and convert to dict format for MetricsEngine.

    Args:
        db: Database session
        account_id: Optional account filter. If None, returns all trades.
        days: Optional period filter. If provided, only returns trades closed in the last N days.
              Use 1=today's session, 3=last 3 days, 7=last week, 30=last month,
              90=last 3 months, 365=last year, None=all time.

    Returns:
        List of trade dictionaries
    """
    query = select(Trade)

    if account_id:
        query = query.where(Trade.account_id == account_id)

    if days is not None:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.where(Trade.close_time >= cutoff)

    query = query.order_by(Trade.close_time.asc())

    result = await db.execute(query)
    trades = result.scalars().all()

    # Convert to dict format
    trades_data = []
    for trade in trades:
        trade_dict = {
            "id": trade.id,
            "account_id": trade.account_id,
            "ticket_id": trade.ticket_id,
            "magic_number": trade.magic_number,
            "symbol": trade.symbol,
            "type": trade.type.value,
            "lots": trade.lots,
            "open_time": trade.open_time,
            "close_time": trade.close_time,
            "open_price": trade.open_price,
            "close_price": trade.close_price,
            "sl": trade.sl,
            "tp": trade.tp,
            "profit_usd": trade.profit_usd,
            "pips": trade.pips,
            "commission": trade.commission,
            "swap": trade.swap,
            "mae": trade.mae,
            "mfe": trade.mfe
        }
        trades_data.append(trade_dict)

    return trades_data


@router.get("/global")
async def get_global_metrics(
    days: Optional[int] = Query(None, description="Filter to last N days. None=all time."),
    db: AsyncSession = Depends(get_db)
):
    """
    Get portfolio-wide metrics aggregated across all accounts.
    Optionally filter by period: days=1,3,7,30,90,365 or None for all time.
    """
    trades_data = await get_trades_for_metrics(db, days=days)
    engine = MetricsEngine(trades_data)

    return engine.get_full_report()

@router.get("/account/{account_id}")
async def get_account_metrics(
    account_id: int,
    days: Optional[int] = Query(None, description="Filter to last N days. None=all time."),
    db: AsyncSession = Depends(get_db)
):
    """
    Get metrics for a specific account.
    Optionally filter by period: days=1,3,7,30,90,365 or None for all time.
    """
    # Verify account exists
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Account not found")

    trades_data = await get_trades_for_metrics(db, account_id, days=days)
    engine = MetricsEngine(trades_data, account=account)

    report_dict = {
        "account": {
            "id": account.id,
            "account_number": account.account_number,
            "broker_name": account.broker_name,
            "alias": account.alias_personalizado
        },
        **engine.get_full_report()
    }
    
    return report_dict


@router.get("/strategy/{magic_number}")
async def get_strategy_metrics(
    magic_number: int,
    account_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get metrics for a specific strategy (magic number).
    Optionally filter by account.
    """
    query = select(Trade).where(Trade.magic_number == magic_number)

    if account_id:
        query = query.where(Trade.account_id == account_id)

    query = query.order_by(Trade.close_time.asc())

    result = await db.execute(query)
    trades = result.scalars().all()

    if not trades:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No trades found for this strategy")

    trades_data = [
        {
            "id": t.id,
            "account_id": t.account_id,
            "ticket_id": t.ticket_id,
            "magic_number": t.magic_number,
            "symbol": t.symbol,
            "type": t.type.value,
            "lots": t.lots,
            "open_time": t.open_time,
            "close_time": t.close_time,
            "open_price": t.open_price,
            "close_price": t.close_price,
            "sl": t.sl,
            "tp": t.tp,
            "profit_usd": t.profit_usd,
            "pips": t.pips,
            "commission": t.commission,
            "swap": t.swap,
            "mae": t.mae,
            "mfe": t.mfe
        }
        for t in trades
    ]

    engine = MetricsEngine(trades_data)

    return {
        "magic_number": magic_number,
        **engine.get_full_report()
    }


@router.get("/equity-curve")
async def get_equity_curve(
    account_id: Optional[int] = None,
    days: Optional[int] = Query(None, description="Filter to last N days."),
    db: AsyncSession = Depends(get_db)
):
    """
    Get equity curve data for charting.
    """
    trades_data = await get_trades_for_metrics(db, account_id, days=days)
    engine = MetricsEngine(trades_data)

    return engine.calculate_equity_curve()


@router.get("/heatmap")
async def get_heatmap(
    account_id: Optional[int] = None,
    days: Optional[int] = Query(None, description="Filter to last N days."),
    db: AsyncSession = Depends(get_db)
):
    """
    Get daily profit heatmap data.
    """
    trades_data = await get_trades_for_metrics(db, account_id, days=days)
    engine = MetricsEngine(trades_data)

    return engine.calculate_daily_heatmap()


@router.get("/temporal")
async def get_temporal_metrics(
    account_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get profit breakdown by time periods (hourly, daily, monthly).
    """
    trades_data = await get_trades_for_metrics(db, account_id)
    engine = MetricsEngine(trades_data)

    return engine.calculate_temporal_metrics()
# hot-reload trigger 04/05/2026 23:42:52
