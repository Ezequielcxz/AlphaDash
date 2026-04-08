"""
Ingestion Router for AlphaDash.

Handles:
- POST /ingest: Receive trade data from MT5 EA via WebRequest
- POST /upload-csv: Parse and import MT5 CSV history exports
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database import get_db
from app.models import Account, Trade
from app.schemas.trade import TradeCreate
from app.services.csv_parser import CSVParser

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/")
async def ingest_trade(
    trade: TradeCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Receive and store a single trade from MT5 EA.

    Creates account if it doesn't exist, then stores the trade.
    Uses ticket_id as unique identifier to prevent duplicates.
    """
    try:
        # Find or create account
        result = await db.execute(
            select(Account).where(Account.account_number == trade.account_number)
        )
        account = result.scalar_one_or_none()

        if not account:
            # Create new account
            from app.schemas.account import AccountType
            account = Account(
                account_number=trade.account_number,
                broker_name=trade.broker_name or "Unknown",
                account_type=AccountType(trade.account_type) if trade.account_type else AccountType.DEMO
            )
            db.add(account)
            await db.flush()

        # Check for duplicate trade
        result = await db.execute(
            select(Trade).where(Trade.ticket_id == trade.ticket_id)
        )
        existing_trade = result.scalar_one_or_none()

        if existing_trade:
            return {
                "status": "duplicate",
                "message": f"Trade {trade.ticket_id} already exists",
                "trade_id": existing_trade.id
            }

        # Create new trade
        new_trade = Trade(
            account_id=account.id,
            ticket_id=trade.ticket_id,
            magic_number=trade.magic_number,
            symbol=trade.symbol,
            type=trade.type,
            lots=trade.lots,
            open_time=trade.open_time,
            close_time=trade.close_time,
            open_price=trade.open_price,
            close_price=trade.close_price,
            sl=trade.sl,
            tp=trade.tp,
            profit_usd=trade.profit_usd,
            pips=trade.pips,
            commission=trade.commission or 0,
            swap=trade.swap or 0,
            mae=trade.mae,
            mfe=trade.mfe
        )
        db.add(new_trade)
        await db.commit()

        return {
            "status": "success",
            "message": f"Trade {trade.ticket_id} ingested successfully",
            "trade_id": new_trade.id,
            "account_id": account.id
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def ingest_batch(
    trades: list[TradeCreate],
    db: AsyncSession = Depends(get_db)
):
    """
    Receive and store multiple trades in batch.

    Useful for initial sync or bulk imports.
    """
    try:
        created_count = 0
        duplicate_count = 0

        for trade in trades:
            # Find or create account
            result = await db.execute(
                select(Account).where(Account.account_number == trade.account_number)
            )
            account = result.scalar_one_or_none()

            if not account:
                from app.schemas.account import AccountType
                account = Account(
                    account_number=trade.account_number,
                    broker_name=trade.broker_name or "Unknown",
                    account_type=AccountType(trade.account_type) if trade.account_type else AccountType.DEMO
                )
                db.add(account)
                await db.flush()

            # Check for duplicate
            result = await db.execute(
                select(Trade).where(Trade.ticket_id == trade.ticket_id)
            )
            if result.scalar_one_or_none():
                duplicate_count += 1
                continue

            # Create trade
            new_trade = Trade(
                account_id=account.id,
                ticket_id=trade.ticket_id,
                magic_number=trade.magic_number,
                symbol=trade.symbol,
                type=trade.type,
                lots=trade.lots,
                open_time=trade.open_time,
                close_time=trade.close_time,
                open_price=trade.open_price,
                close_price=trade.close_price,
                sl=trade.sl,
                tp=trade.tp,
                profit_usd=trade.profit_usd,
                pips=trade.pips,
                commission=trade.commission or 0,
                swap=trade.swap or 0,
                mae=trade.mae,
                mfe=trade.mfe
            )
            db.add(new_trade)
            created_count += 1

        await db.commit()

        return {
            "status": "success",
            "created": created_count,
            "duplicates": duplicate_count,
            "total_received": len(trades)
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-csv")
async def upload_csv(
    file_content: bytes,
    account_number: int,
    broker_name: Optional[str] = "Unknown",
    db: AsyncSession = Depends(get_db)
):
    """
    Parse and import MT5 CSV trade history.

    Accepts raw CSV file content and parses it using CSVParser.
    """
    try:
        # Parse CSV
        parser = CSVParser()
        result = parser.parse(file_content, account_number)

        if not result["success"]:
            return {
                "status": "error",
                "errors": result["errors"]
            }

        # Find or create account
        result_db = await db.execute(
            select(Account).where(Account.account_number == account_number)
        )
        account = result_db.scalar_one_or_none()

        if not account:
            from app.schemas.account import AccountType
            account = Account(
                account_number=account_number,
                broker_name=broker_name,
                account_type=AccountType.DEMO
            )
            db.add(account)
            await db.flush()

        # Insert trades
        created_count = 0
        duplicate_count = 0

        for trade_data in result["trades"]:
            # Check for duplicate
            result_db = await db.execute(
                select(Trade).where(Trade.ticket_id == trade_data["ticket_id"])
            )
            if result_db.scalar_one_or_none():
                duplicate_count += 1
                continue

            new_trade = Trade(
                account_id=account.id,
                **trade_data
            )
            db.add(new_trade)
            created_count += 1

        await db.commit()

        return {
            "status": "success",
            "account_id": account.id,
            "created": created_count,
            "duplicates": duplicate_count,
            "total_parsed": result["total_parsed"]
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))