"""
Utility functions for trading calculations.
"""
from typing import Optional, Tuple


# Pip values by symbol type
PIP_MULTIPLIERS = {
    "JPY": 0.01,  # JPY pairs: 1 pip = 0.01
    "STANDARD": 0.0001,  # Standard forex: 1 pip = 0.0001
    "INDEX": 0.1,  # Indices
    "COMMODITY": 0.01,  # Commodities
    "CRYPTO": 0.01,  # Cryptocurrencies
}


def get_symbol_type(symbol: str) -> str:
    """
    Determine symbol type for pip calculation.

    Args:
        symbol: Trading symbol (e.g., EURUSD, USDJPY, XAUUSD)

    Returns:
        Symbol type string
    """
    symbol = symbol.upper()

    # JPY pairs
    if "JPY" in symbol:
        return "JPY"

    # Gold/Silver
    if symbol.startswith("XAU") or symbol.startswith("XAG"):
        return "COMMODITY"

    # Indices
    index_prefixes = ["US", "GER", "UK", "JP", "AU", "EU"]
    for prefix in index_prefixes:
        if symbol.startswith(prefix) and len(symbol) <= 10:
            return "INDEX"

    # Crypto
    crypto_symbols = ["BTC", "ETH", "XRP", "LTC", "BNB"]
    for crypto in crypto_symbols:
        if symbol.startswith(crypto) or symbol.endswith(crypto):
            return "CRYPTO"

    return "STANDARD"


def calculate_pips(
    entry_price: float,
    exit_price: float,
    symbol: str,
    direction: str = "buy"
) -> float:
    """
    Calculate profit/loss in pips.

    Args:
        entry_price: Entry price
        exit_price: Exit price
        symbol: Trading symbol
        direction: Trade direction (buy/sell)

    Returns:
        Pips gained or lost (positive for profit, negative for loss)
    """
    symbol_type = get_symbol_type(symbol)
    pip_multiplier = PIP_MULTIPLIERS.get(symbol_type, 0.0001)

    price_diff = exit_price - entry_price

    if direction.lower() == "sell":
        price_diff = -price_diff

    return round(price_diff / pip_multiplier, 1)


def calculate_rr_ratio(
    entry: float,
    stop_loss: Optional[float],
    take_profit: Optional[float],
    direction: str = "buy"
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate risk/reward ratio.

    Args:
        entry: Entry price
        stop_loss: Stop loss price
        take_profit: Take profit price
        direction: Trade direction (buy/sell)

    Returns:
        Tuple of (risk_pips, reward_pips)
    """
    if stop_loss is None or take_profit is None:
        return None, None

    if direction.lower() == "buy":
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
    else:
        risk = abs(stop_loss - entry)
        reward = abs(entry - take_profit)

    return risk, reward


def calculate_position_size(
    account_balance: float,
    risk_percent: float,
    stop_loss_pips: float,
    pip_value: float = 10.0  # Default for standard lot
) -> float:
    """
    Calculate position size based on risk percentage.

    Args:
        account_balance: Current account balance
        risk_percent: Risk percentage (e.g., 1.0 for 1%)
        stop_loss_pips: Stop loss distance in pips
        pip_value: Value per pip per lot

    Returns:
        Position size in lots
    """
    risk_amount = account_balance * (risk_percent / 100)
    risk_per_lot = stop_loss_pips * pip_value

    if risk_per_lot <= 0:
        return 0

    return round(risk_amount / risk_per_lot, 2)