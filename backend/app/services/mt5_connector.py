"""
MetaTrader5 Connection Service.

Handles direct connection to MT5 terminals for automatic trade synchronization.
Supports multiple MT5 installations via explicit terminal path selection.
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
import os

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


def find_mt5_terminals() -> List[Dict[str, str]]:
    """
    Scan running processes for MT5 terminal instances.

    Returns:
        List of dicts with 'path', 'name', and 'pid'
    """
    terminals = []

    if not PSUTIL_AVAILABLE:
        logger.warning("psutil not available - cannot auto-detect MT5 terminals")
        return terminals

    try:
        seen_paths = set()
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                pname = (proc.info.get('name', '') or '').lower()
                pexe  = proc.info.get('exe',  '') or ''

                # Only match MetaTrader terminal executables, not Windows Terminal or others
                is_mt5 = pname in ('terminal64.exe', 'terminal.exe')
                # Extra guard: path must not be under WindowsApps (Windows Terminal)
                is_windows_app = 'windowsapps' in pexe.lower()

                if is_mt5 and not is_windows_app and pexe and pexe not in seen_paths:
                    seen_paths.add(pexe)
                    folder = os.path.basename(os.path.dirname(pexe))
                    terminals.append({
                        'path': pexe,
                        'name': folder,
                        'pid':  str(proc.info['pid']),
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        logger.error(f"Error scanning MT5 terminals: {e}")


    logger.info(f"Found {len(terminals)} MT5 terminal(s): {[t['path'] for t in terminals]}")
    return terminals


class ConnectionStatus(str, Enum):
    """MT5 Connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MT5Credentials:
    """MT5 connection credentials."""
    login: int
    password: str
    server: str
    timeout: int = 60000
    path: Optional[str] = None  # explicit terminal exe path; None = auto-detect


@dataclass
class SyncResult:
    """Result of a sync operation."""
    success: bool
    account_id: Optional[int] = None
    total_trades: int = 0
    new_trades: int = 0
    updated_trades: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class MT5Connector:
    """
    Manages connection to MetaTrader5 terminal.

    Usage:
        connector = MT5Connector()
        await connector.connect(login, password, server)
        trades = await connector.get_trade_history()
        await connector.disconnect()
    """

    def __init__(self):
        self._connected = False
        self._account_info = None
        self._credentials: Optional[MT5Credentials] = None
        self._last_sync_time: Optional[datetime] = None

    @property
    def is_connected(self) -> bool:
        """Check if connected to MT5."""
        return self._connected and mt5.terminal_info() is not None

    @property
    def account_info(self) -> Optional[Dict[str, Any]]:
        """Get current account info."""
        return self._account_info

    @property
    def connection_status(self) -> ConnectionStatus:
        """Get current connection status."""
        if self.is_connected:
            return ConnectionStatus.CONNECTED
        elif self._credentials:
            return ConnectionStatus.CONNECTING
        return ConnectionStatus.DISCONNECTED

    async def connect(
        self,
        login: int,
        password: str,
        server: str,
        timeout: int = 60000,
        path: Optional[str] = None
    ) -> SyncResult:
        """
        Connect to MT5 terminal.

        Args:
            login:    MT5 account number
            password: Account password
            server:   Broker server name
            timeout:  Connection timeout in milliseconds
            path:     Full path to terminal64.exe. If None, auto-detects.
                      With multiple MT5 installations you MUST specify this
                      to avoid connecting to the wrong terminal.

        Returns:
            SyncResult with connection status
        """
        self._credentials = MT5Credentials(
            login=login,
            password=password,
            server=server,
            timeout=timeout,
            path=path
        )

        try:
            # If no path given, try to auto-detect the correct terminal.
            # When multiple terminals are running it's ambiguous, so we
            # warn the caller.
            if not path:
                terminals = find_mt5_terminals()
                if len(terminals) > 1:
                    logger.warning(
                        f"{len(terminals)} MT5 terminals running. "
                        "Connecting to the first one. "
                        "Pass 'path' to select a specific terminal."
                    )
                if terminals:
                    path = terminals[0]['path']
                    logger.info(f"Auto-selected terminal: {path}")

            # Step 1: Initialize WITHOUT credentials to reuse the terminal's
            # existing logged-in session. This is the recommended approach when
            # the terminal is already open and authenticated.
            if path:
                initialized = mt5.initialize(path, timeout=timeout)
            else:
                initialized = mt5.initialize()

            if not initialized:
                error = mt5.last_error()
                logger.error(f"MT5 initialize (no-creds) failed: {error}")
                return SyncResult(
                    success=False,
                    errors=[f"MT5 initialize failed: {error}"]
                )

            # Step 2: Check which account is currently active
            account_info = mt5.account_info()
            if account_info is not None and account_info.login == login:
                # Terminal is already logged into the requested account - done!
                logger.info(f"Terminal already logged into {login}@{server}, reusing session")
            else:
                # Terminal is logged into a different account (or not logged in)
                # → do an explicit login with credentials
                if not password:
                    mt5.shutdown()
                    return SyncResult(
                        success=False,
                        errors=["Terminal is not logged into this account. Please enter your password."]
                    )
                if not mt5.login(login, password, server):
                    error = mt5.last_error()
                    logger.error(f"MT5 login failed: {error}")
                    mt5.shutdown()
                    return SyncResult(
                        success=False,
                        errors=[f"Login failed: {error}"]
                    )
                account_info = mt5.account_info()

            if account_info is None:
                error = mt5.last_error()
                logger.error(f"Failed to get account info: {error}")
                return SyncResult(
                    success=False,
                    errors=[f"Failed to get account info after login: {error}"]
                )

            self._account_info = {
                "login": account_info.login,
                "name": account_info.name,
                "server": account_info.server,
                "currency": account_info.currency,
                "balance": account_info.balance,
                "credit": getattr(account_info, 'credit', 0.0),
                "equity": account_info.equity,
                "margin": account_info.margin,
                "margin_free": account_info.margin_free,
                "margin_level": account_info.margin_level,
                "profit": account_info.profit,
                "company": account_info.company,
            }

            self._connected = True
            logger.info(f"Connected to MT5: {login}@{server} via {path or 'auto'}")

            return SyncResult(
                success=True,
                errors=[]
            )

        except Exception as e:
            logger.exception(f"MT5 connection error: {e}")
            return SyncResult(
                success=False,
                errors=[str(e)]
            )

    async def disconnect(self) -> None:
        """Disconnect from MT5 terminal."""
        if self._connected:
            mt5.shutdown()
            self._connected = False
            self._account_info = None
            logger.info("Disconnected from MT5")

    async def get_trade_history(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get historical trades from MT5.

        Args:
            from_date: Start date (default: 30 days ago)
            to_date: End date (default: now)

        Returns:
            List of trade dictionaries
        """
        if not self.is_connected:
            logger.error("Not connected to MT5")
            return []

        # Default date range
        if from_date is None:
            from_date = datetime.now() - timedelta(days=30)
        if to_date is None:
            to_date = datetime.now()

        try:
            # Get history deals
            logger.info(f"[get_trade_history] calling mt5.history_deals_get({from_date}, {to_date})")
            logger.info(f"[get_trade_history] mt5 module: {mt5}")
            logger.info(f"[get_trade_history] terminal_info: {mt5.terminal_info()}")
            deals = mt5.history_deals_get(from_date, to_date)
            logger.info(f"[get_trade_history] result: {deals} last_error: {mt5.last_error()}")

            if deals is None:
                error = mt5.last_error()
                logger.warning(f"MT5 history_deals_get returned None: {error}")
                return []

            total_deals = len(deals)
            logger.info(f"MT5 returned {total_deals} total deals in range {from_date} - {to_date}")

            if total_deals == 0:
                logger.info("No deals at all in the specified date range")
                return []

            # Build a position -> opening deal map from the deals we already have
            # (avoids a second MT5 call per position which can fail)
            opening_by_position: dict = {}
            for deal in deals:
                if deal.entry == mt5.DEAL_ENTRY_IN:
                    # Keep the latest IN deal per position (in case of partial closes)
                    opening_by_position[deal.position_id] = deal

            trades = []
            skipped_entries = 0
            skipped_balance = 0

            for deal in deals:
                # Only process deals with actual profit (closed positions)
                if deal.entry not in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY):
                    skipped_entries += 1
                    continue

                # Skip balance operations
                if deal.type in (mt5.DEAL_TYPE_BALANCE, mt5.DEAL_TYPE_CREDIT):
                    skipped_balance += 1
                    continue

                # Find the opening deal from our pre-built map
                open_deal = opening_by_position.get(deal.position_id)

                trade = {
                    "ticket_id": deal.ticket,
                    "position_id": deal.position_id,
                    "order_ticket": deal.order,
                    "symbol": deal.symbol,
                    "type": "Buy" if deal.type == mt5.DEAL_TYPE_BUY else "Sell",
                    "magic_number": deal.magic,
                    "lots": deal.volume,
                    "open_price": open_deal.price if open_deal else deal.price,
                    "open_time": datetime.fromtimestamp(open_deal.time) if open_deal else datetime.fromtimestamp(deal.time),
                    "close_price": deal.price,
                    "close_time": datetime.fromtimestamp(deal.time),
                    "profit_usd": deal.profit,
                    "commission": deal.commission,
                    "swap": deal.swap,
                    "sl": 0.0,
                    "tp": 0.0,
                    "pips": None,
                    "mae": None,
                    "mfe": None,
                    "fee": deal.fee if hasattr(deal, 'fee') else 0,
                    "comment": deal.comment if hasattr(deal, 'comment') else "",
                }


                # Calculate pips
                trade["pips"] = self._calculate_pips(
                    trade["open_price"],
                    trade["close_price"],
                    trade["symbol"],
                    trade["type"]
                )

                trades.append(trade)

            logger.info(
                f"Result: {len(trades)} closing trades | "
                f"{skipped_entries} skipped (not OUT) | "
                f"{skipped_balance} skipped (balance ops) | "
                f"{total_deals} total deals"
            )
            return trades

        except Exception as e:
            logger.exception(f"Error in get_trade_history: {e}")
            return []

    def _find_opening_deal(self, position_id: int) -> Optional[Any]:
        """Find the opening deal for a position. (Deprecated: use opening_by_position map instead)"""
        try:
            deals = mt5.history_deals_get(position=position_id)
            if deals:
                for deal in deals:
                    if deal.entry == mt5.DEAL_ENTRY_IN:
                        return deal
        except Exception as e:
            logger.warning(f"_find_opening_deal({position_id}) failed: {e}")
        return None


    def _calculate_pips(self, open_price: float, close_price: float, symbol: str, trade_type: str) -> float:
        """Calculate pips based on symbol type."""
        pip_multiplier = 0.0001  # Standard forex

        if "JPY" in symbol:
            pip_multiplier = 0.01
        elif symbol.startswith("XAU") or symbol.startswith("XAG"):
            pip_multiplier = 0.01
        elif any(x in symbol for x in ["US", "GER", "UK", "JP"]):
            pip_multiplier = 0.1
        elif any(x in symbol for x in ["BTC", "ETH", "XRP"]):
            pip_multiplier = 0.01

        price_diff = close_price - open_price
        if trade_type == "Sell":
            price_diff = -price_diff

        return round(price_diff / pip_multiplier, 1)

    async def get_account_summary(self) -> Dict[str, Any]:
        """Get current account summary."""
        if not self.is_connected:
            return {}

        account_info = mt5.account_info()
        if account_info is None:
            return {}

        return {
            "login": account_info.login,
            "name": account_info.name,
            "server": account_info.server,
            "currency": account_info.currency,
            "balance": account_info.balance,
            "equity": account_info.equity,
            "margin": account_info.margin,
            "free_margin": account_info.margin_free,
            "margin_level": account_info.margin_level,
            "profit": account_info.profit,
            "company": account_info.company,
        }

    async def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get currently open positions."""
        if not self.is_connected:
            return []

        positions = mt5.positions_get()
        if positions is None:
            return []

        result = []
        for pos in positions:
            result.append({
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": "Buy" if pos.type == mt5.POSITION_TYPE_BUY else "Sell",
                "volume": pos.volume,
                "open_price": pos.price_open,
                "current_price": pos.price_current,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": pos.profit,
                "swap": pos.swap,
                "magic": pos.magic,
                "comment": pos.comment,
                "open_time": datetime.fromtimestamp(pos.time),
            })

        return result

    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information."""
        if not self.is_connected:
            return None

        info = mt5.symbol_info(symbol)
        if info is None:
            return None

        return {
            "symbol": info.name,
            "bid": info.bid,
            "ask": info.ask,
            "point": info.point,
            "digits": info.digits,
            "spread": info.spread,
            "contract_size": info.trade_contract_size,
            "min_lot": info.volume_min,
            "max_lot": info.volume_max,
            "lot_step": info.volume_step,
        }


# Singleton instance for background sync
_mt5_connector: Optional[MT5Connector] = None


def get_mt5_connector() -> MT5Connector:
    """Get MT5 connector singleton."""
    global _mt5_connector
    if _mt5_connector is None:
        _mt5_connector = MT5Connector()
    return _mt5_connector