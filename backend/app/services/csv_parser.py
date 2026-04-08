"""
CSV Parser for MT5 trade history imports.

Handles parsing of MT5 exported trade history files.
"""
import pandas as pd
from datetime import datetime
from typing import Optional
import io


class CSVParser:
    """Parser for MT5 exported trade history CSV files."""

    # Standard MT5 column names (may vary by broker)
    COLUMN_MAPPINGS = {
        'Ticket': 'ticket_id',
        'Position': 'ticket_id',
        'Time': 'open_time',
        'Time Open': 'open_time',
        'Open Time': 'open_time',
        'Time Close': 'close_time',
        'Close Time': 'close_time',
        'Symbol': 'symbol',
        'Type': 'type',
        'Volume': 'lots',
        'Price': 'open_price',
        'Price Open': 'open_price',
        'Open Price': 'open_price',
        'Price Close': 'close_price',
        'Close Price': 'close_price',
        'SL': 'sl',
        'TP': 'tp',
        'Profit': 'profit_usd',
        'Commission': 'commission',
        'Swap': 'swap',
        'Magic': 'magic_number',
        'Comment': 'comment',
        'MAE': 'mae',
        'MFE': 'mfe'
    }

    def parse(self, file_content: bytes, account_number: int) -> dict:
        """
        Parse MT5 exported CSV file.

        Args:
            file_content: Raw CSV file content
            account_number: MT5 account number

        Returns:
            Dictionary with parsed trades data
        """
        try:
            # Read CSV
            df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')

            # Try alternative encodings if utf-8 fails
            if df.empty or len(df.columns) == 1:
                df = pd.read_csv(io.BytesIO(file_content), encoding='latin-1')

            # Clean column names
            df.columns = df.columns.str.strip()

            # Map columns to standard names
            df = self._map_columns(df)

            # Filter only closed positions (exclude pending orders, balance adjustments)
            df = self._filter_closed_trades(df)

            # Parse and transform data
            trades = self._transform_trades(df, account_number)

            return {
                "success": True,
                "trades": trades,
                "total_parsed": len(trades),
                "errors": []
            }

        except Exception as e:
            return {
                "success": False,
                "trades": [],
                "total_parsed": 0,
                "errors": [str(e)]
            }

    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map CSV columns to standard names."""
        column_map = {}
        for col in df.columns:
            if col in self.COLUMN_MAPPINGS:
                column_map[col] = self.COLUMN_MAPPINGS[col]

        return df.rename(columns=column_map)

    def _filter_closed_trades(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter to include only closed trades."""
        # Filter by type if type column exists
        if 'type' in df.columns:
            # Keep only buy/sell positions
            valid_types = ['buy', 'sell', 'Buy', 'Sell', 'buy limit', 'buy stop',
                          'sell limit', 'sell stop', 'Buy Limit', 'Buy Stop',
                          'Sell Limit', 'Sell Stop']
            df = df[df['type'].str.lower().str.strip().isin([t.lower() for t in valid_types])]

        return df

    def _transform_trades(self, df: pd.DataFrame, account_number: int) -> list[dict]:
        """Transform dataframe to list of trade dictionaries."""
        trades = []

        for _, row in df.iterrows():
            try:
                trade = {
                    "ticket_id": self._parse_int(row.get('ticket_id')),
                    "account_number": account_number,
                    "magic_number": self._parse_int(row.get('magic_number')),
                    "symbol": str(row.get('symbol', '')).strip(),
                    "type": self._parse_trade_type(row.get('type')),
                    "lots": self._parse_float(row.get('lots')),
                    "open_time": self._parse_datetime(row.get('open_time')),
                    "close_time": self._parse_datetime(row.get('close_time')),
                    "open_price": self._parse_float(row.get('open_price')),
                    "close_price": self._parse_float(row.get('close_price')),
                    "sl": self._parse_float(row.get('sl'), allow_none=True),
                    "tp": self._parse_float(row.get('tp'), allow_none=True),
                    "profit_usd": self._parse_float(row.get('profit_usd')),
                    "commission": self._parse_float(row.get('commission'), default=0),
                    "swap": self._parse_float(row.get('swap'), default=0),
                    "mae": self._parse_float(row.get('mae'), allow_none=True),
                    "mfe": self._parse_float(row.get('mfe'), allow_none=True),
                    "pips": None  # Calculate later
                }

                # Validate required fields
                if trade['ticket_id'] and trade['symbol'] and trade['open_time'] and trade['close_time']:
                    trades.append(trade)

            except Exception as e:
                continue

        return trades

    def _parse_trade_type(self, value) -> str:
        """Parse trade type to standardized format."""
        if pd.isna(value):
            return "Buy"

        type_str = str(value).lower().strip()

        if 'sell' in type_str:
            return "Sell"
        return "Buy"

    def _parse_datetime(self, value) -> datetime:
        """Parse datetime from various formats."""
        if pd.isna(value):
            return datetime.now()

        if isinstance(value, datetime):
            return value

        # Try common formats
        formats = [
            '%Y.%m.%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%d.%m.%Y %H:%M:%S',
            '%Y.%m.%d %H:%M',
            '%Y-%m-%d %H:%M',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(value).strip(), fmt)
            except ValueError:
                continue

        # Fallback to pandas parsing
        try:
            return pd.to_datetime(value).to_pydatetime()
        except:
            return datetime.now()

    def _parse_float(self, value, default: float = 0, allow_none: bool = False) -> Optional[float]:
        """Parse float value."""
        if pd.isna(value):
            return None if allow_none else default

        try:
            return float(value)
        except (ValueError, TypeError):
            return None if allow_none else default

    def _parse_int(self, value, default: int = 0) -> Optional[int]:
        """Parse integer value."""
        if pd.isna(value):
            return default

        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default