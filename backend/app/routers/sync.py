"""
MT5 Sync Router for AlphaDash.

Handles:
- POST /sync/connect: Connect to MT5 with credentials
- POST /sync/disconnect: Disconnect from MT5
- POST /sync/history: Download trade history
- GET /sync/status: Get connection status
- GET /sync/positions: Get open positions
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import asyncio
import logging

from app.database import get_db
from app.models import Account, Trade
from app.services.mt5_connector import (
    MT5Connector,
    MT5Credentials,
    get_mt5_connector,
    ConnectionStatus,
    find_mt5_terminals,
)

router = APIRouter(prefix="/sync", tags=["mt5-sync"])
logger = logging.getLogger(__name__)


# Request/Response Models
class ConnectRequest(BaseModel):
    """MT5 connection credentials."""
    login: int = Field(..., description="MT5 account number")
    password: str = Field(..., description="Account password")
    server: str = Field(..., description="Broker server name")
    timeout: int = Field(60000, description="Connection timeout in ms")
    path: Optional[str] = Field(None, description="Path to terminal64.exe (required when multiple MT5 installs exist)")


class SyncRequest(BaseModel):
    """Trade sync request."""
    login: int
    password: str
    server: str
    from_date: Optional[datetime] = Field(None, description="Start date for history")
    to_date: Optional[datetime] = Field(None, description="End date for history")
    days_back: int = Field(30, description="Days to sync if no date provided")
    path: Optional[str] = Field(None, description="Path to terminal64.exe")


class TerminalInfo(BaseModel):
    """Detected MT5 terminal instance."""
    path: str
    name: str
    pid: str


class ConnectionResponse(BaseModel):
    """Connection status response."""
    connected: bool
    login: Optional[int] = None
    server: Optional[str] = None
    balance: Optional[float] = None
    equity: Optional[float] = None
    currency: Optional[str] = None


class SyncResponse(BaseModel):
    """Sync operation response."""
    success: bool
    account_id: Optional[int] = None
    total_trades: int = 0
    new_trades: int = 0
    errors: list[str] = []


# Global sync status storage
_sync_status: dict[int, dict] = {}


@router.get("/terminals", response_model=list[TerminalInfo])
async def list_mt5_terminals():
    """
    Detect all currently running MT5 terminal processes.

    Returns a list of terminal paths so the frontend can let
    the user pick which terminal to connect to.
    """
    terminals = find_mt5_terminals()
    return terminals


@router.get("/diagnose")
async def diagnose_mt5():
    """Run full MT5 diagnostic from within the FastAPI process."""
    import MetaTrader5 as mt5
    from datetime import timedelta
    from collections import Counter

    connector = get_mt5_connector()
    result = {
        "connector_connected": connector.is_connected,
        "account_info": connector.account_info,
        "mt5_terminal_info": None,
        "deals_last_365": None,
        "deals_entry_breakdown": {},
        "importable_trades": 0,
        "last_error": None,
    }

    try:
        if connector.is_connected:
            tinfo = mt5.terminal_info()
            if tinfo:
                result["mt5_terminal_info"] = {
                    "name": tinfo.name,
                    "connected": tinfo.connected,
                    "company": tinfo.company,
                }

            from_date = datetime.now() - timedelta(days=365)
            to_date = datetime.now()

            # Test 1: raw mt5.history_deals_get
            deals = mt5.history_deals_get(from_date, to_date)
            if deals is None:
                result["last_error"] = str(mt5.last_error())
            else:
                result["deals_last_365"] = len(deals)
                entry_map = {
                    mt5.DEAL_ENTRY_IN: "IN",
                    mt5.DEAL_ENTRY_OUT: "OUT",
                    mt5.DEAL_ENTRY_INOUT: "INOUT",
                    mt5.DEAL_ENTRY_OUT_BY: "OUT_BY",
                }
                breakdown = Counter(d.entry for d in deals)
                result["deals_entry_breakdown"] = {
                    entry_map.get(k, str(k)): v for k, v in breakdown.items()
                }
                importable = [
                    d for d in deals
                    if d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY)
                    and d.type not in (mt5.DEAL_TYPE_BALANCE, mt5.DEAL_TYPE_CREDIT)
                ]
                result["importable_trades"] = len(importable)
                if importable:
                    d = importable[0]
                    result["first_importable"] = {
                        "symbol": d.symbol,
                        "profit": d.profit,
                        "time": datetime.fromtimestamp(d.time).isoformat(),
                    }

            # Test 2: connector.get_trade_history() - the actual method used by /history
            connector_trades = await connector.get_trade_history(from_date, to_date)
            result["connector_get_trade_history_count"] = len(connector_trades)
            if connector_trades:
                result["connector_first_trade"] = {
                    "symbol": connector_trades[0].get("symbol"),
                    "profit": connector_trades[0].get("profit_usd"),
                }

    except Exception as e:
        result["error"] = str(e)

    return result

@router.post("/connect", response_model=ConnectionResponse)
async def connect_mt5(
    request: ConnectRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Connect to MT5 terminal with provided credentials.

    This will:
    1. Initialize MT5 connection
    2. Login to the account
    3. Create/update account in database
    4. Return connection status
    """
    connector = get_mt5_connector()

    # Connect to MT5 — pass path so the correct terminal is used
    result = await connector.connect(
        login=request.login,
        password=request.password,
        server=request.server,
        timeout=request.timeout,
        path=request.path or None
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=f"MT5 connection failed: {', '.join(result.errors)}"
        )

    account_info = connector.account_info

    if account_info:
        # Create or update account in database
        db_result = await db.execute(
            select(Account).where(Account.account_number == request.login)
        )
        account = db_result.scalar_one_or_none()

        if not account:
            account = Account(
                account_number=request.login,
                broker_name=account_info.get("company", request.server),
                account_type="Real",
                alias_personalizado=account_info.get("name"),
                balance_inicial=account_info.get("balance", 0),
                credito=account_info.get("credit", 0),
                current_balance=account_info.get("balance", 0),
                current_equity=account_info.get("equity", 0)
            )
            db.add(account)
        else:
            # Always update broker metadata from the live terminal data
            account.broker_name = account_info.get("company", account.broker_name)
            account.alias_personalizado = account_info.get("name", account.alias_personalizado)
            account.credito = account_info.get("credit", 0)
            account.current_balance = account_info.get("balance", 0)
            account.current_equity = account_info.get("equity", 0)

        await db.commit()
        await db.refresh(account)

    return ConnectionResponse(
        connected=connector.is_connected,
        login=account_info.get("login") if account_info else None,
        server=account_info.get("server") if account_info else None,
        balance=account_info.get("balance") if account_info else None,
        equity=account_info.get("equity") if account_info else None,
        currency=account_info.get("currency") if account_info else None
    )


@router.post("/disconnect")
async def disconnect_mt5():
    """Disconnect from MT5 terminal."""
    connector = get_mt5_connector()
    await connector.disconnect()

    return {"status": "disconnected"}


@router.get("/status", response_model=ConnectionResponse)
async def get_connection_status():
    """Get current MT5 connection status."""
    connector = get_mt5_connector()

    if connector.is_connected:
        account_info = connector.account_info or {}
        return ConnectionResponse(
            connected=True,
            login=account_info.get("login"),
            server=account_info.get("server"),
            balance=account_info.get("balance"),
            equity=account_info.get("equity"),
            currency=account_info.get("currency")
        )

    return ConnectionResponse(connected=False)


@router.post("/history", response_model=SyncResponse)
async def sync_trade_history(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Download and import trade history from MT5.

    This endpoint:
    1. Connects to MT5 (if not already connected)
    2. Downloads trade history
    3. Imports trades to database
    4. Returns sync results
    """
    connector = get_mt5_connector()

    # If already connected to the correct account, reuse the session
    if connector.is_connected:
        current_login = (connector.account_info or {}).get("login")
        if current_login and current_login == request.login:
            logger.info(f"Reusing existing MT5 session for account {request.login}")
        else:
            # Connected to a different account - reconnect
            if not request.password:
                raise HTTPException(
                    status_code=400,
                    detail="Session expired. Please re-enter your password and click Connect first."
                )
            result = await connector.connect(
                login=request.login,
                password=request.password,
                server=request.server,
                path=request.path or None
            )
            if not result.success:
                raise HTTPException(
                    status_code=400,
                    detail=f"MT5 connection failed: {', '.join(result.errors)}"
                )

    else:
        # Not connected at all
        if not request.password:
            raise HTTPException(
                status_code=400,
                detail="Not connected to MT5. Please enter your password and click 'Connect' before syncing."
            )

        # Try to connect using the terminal path selected by user
        result = await connector.connect(
            login=request.login,
            password=request.password,
            server=request.server,
            path=request.path or None
        )

        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=f"MT5 connection failed: {', '.join(result.errors)}"
            )

    # Get trade history
    from datetime import timedelta

    from_date = request.from_date
    if from_date is None:
        from_date = datetime.now() - timedelta(days=request.days_back)

    to_date = request.to_date or datetime.now()

    trades = await connector.get_trade_history(from_date, to_date)

    if not trades:
        return SyncResponse(
            success=True,
            total_trades=0,
            new_trades=0,
            errors=["No closed trades found in the specified date range. Make sure MT5 terminal has historical data loaded and trades are closed (not just open positions)."]
        )

    # Find or create account
    db_result = await db.execute(
        select(Account).where(Account.account_number == request.login)
    )
    account = db_result.scalar_one_or_none()

    account_info = connector.account_info or {}

    if not account:
        account = Account(
            account_number=request.login,
            broker_name=request.server,
            account_type="Real",
            alias_personalizado=account_info.get("name"),
            balance_inicial=account_info.get("balance", 0),
            credito=account_info.get("credit", 0),
            current_balance=account_info.get("balance", 0),
            current_equity=account_info.get("equity", 0)
        )
        db.add(account)
        await db.flush()
    else:
        account.credito = account_info.get("credit", account.credito)
        account.current_balance = account_info.get("balance", account.current_balance)
        account.current_equity = account_info.get("equity", account.current_equity)
        await db.flush()

    # Import trades
    new_trades = 0
    errors = []

    for trade_data in trades:
        try:
            # Check if trade already exists
            existing = await db.execute(
                select(Trade).where(Trade.ticket_id == trade_data["ticket_id"])
            )
            if existing.scalar_one_or_none():
                continue  # Skip duplicate

            # Create trade record
            trade = Trade(
                account_id=account.id,
                ticket_id=trade_data["ticket_id"],
                magic_number=trade_data.get("magic_number"),
                symbol=trade_data["symbol"],
                type=trade_data["type"],
                lots=trade_data["lots"],
                open_time=trade_data["open_time"],
                close_time=trade_data["close_time"],
                open_price=trade_data["open_price"],
                close_price=trade_data["close_price"],
                sl=trade_data.get("sl", 0),
                tp=trade_data.get("tp", 0),
                profit_usd=trade_data["profit_usd"],
                pips=trade_data.get("pips"),
                commission=trade_data.get("commission", 0),
                swap=trade_data.get("swap", 0),
                mae=trade_data.get("mae"),
                mfe=trade_data.get("mfe")
            )
            db.add(trade)
            new_trades += 1

        except Exception as e:
            errors.append(f"Error importing trade {trade_data.get('ticket_id')}: {str(e)}")
            logger.error(f"Trade import error: {e}")

    await db.commit()

    # Update sync status
    _sync_status[request.login] = {
        "last_sync": datetime.now(),
        "trades_synced": new_trades,
        "status": "completed"
    }

    return SyncResponse(
        success=True,
        account_id=account.id,
        total_trades=len(trades),
        new_trades=new_trades,
        errors=errors
    )


@router.get("/positions")
async def get_open_positions():
    """Get currently open positions from MT5."""
    connector = get_mt5_connector()

    if not connector.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to MT5")

    positions = await connector.get_open_positions()

    return {
        "total": len(positions),
        "positions": positions
    }


@router.get("/summary")
async def get_account_summary():
    """Get account summary from MT5."""
    connector = get_mt5_connector()

    if not connector.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to MT5")

    summary = await connector.get_account_summary()

    return summary


@router.get("/symbols/{symbol}")
async def get_symbol_info(symbol: str):
    """Get symbol information from MT5."""
    connector = get_mt5_connector()

    if not connector.is_connected:
        raise HTTPException(status_code=400, detail="Not connected to MT5")

    info = await connector.get_symbol_info(symbol.upper())

    if info is None:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

    return info


@router.get("/sync-status/{login}")
async def get_sync_status(login: int):
    """Get last sync status for an account."""
    status = _sync_status.get(login, {
        "status": "never_synced",
        "last_sync": None
    })

    return status