"""
Metrics Engine for AlphaDash.

Calculates comprehensive trading performance metrics including:
- Core metrics: Win Rate, Profit Factor, Expectancy, Recovery Factor
- Risk metrics: Max Drawdown, Sharpe Ratio, Sortino Ratio
- Temporal analysis: Profit by hour, day, month
- Strategy grouping: Metrics by Magic Number
"""
import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime
from collections import defaultdict


class MetricsEngine:
    """Engine for calculating trading performance metrics."""

    def __init__(self, trades_data: list[dict], account=None):
        """
        Initialize metrics engine with trade data.

        Args:
            trades_data: List of trade dictionaries from database
            account: Optional Account object for exact equity calculation
        """
        self.account = account
        if not trades_data:
            self.df = pd.DataFrame()
            self.is_empty = True
        else:
            self.df = pd.DataFrame(trades_data)
            self.is_empty = False

            # Ensure datetime columns
            if 'close_time' in self.df.columns:
                self.df['close_time'] = pd.to_datetime(self.df['close_time'])
            if 'open_time' in self.df.columns:
                self.df['open_time'] = pd.to_datetime(self.df['open_time'])

            # Sort by close time
            if 'close_time' in self.df.columns:
                self.df = self.df.sort_values('close_time').reset_index(drop=True)

    def calculate_equity_curve(self) -> dict:
        """
        Calculate equity curve data for visualization.

        Returns:
            Dictionary with dates and cumulative equity values
        """
        if self.is_empty:
            return {"dates": [], "equity": [], "drawdown": []}

        # Calculate cumulative profit
        self.df['cumulative_profit'] = self.df['profit_usd'].cumsum()

        # Calculate running max for drawdown
        self.df['running_max'] = self.df['cumulative_profit'].cummax()
        self.df['drawdown'] = self.df['cumulative_profit'] - self.df['running_max']

        # Get initial balance
        if self.account and hasattr(self.account, 'current_balance'):
            base_balance = (self.account.current_balance or 0.0) + (self.account.credito or 0.0)
            # Anchor the end of the curve to the current true balance
            total_profit = self.df['profit_usd'].sum()
            initial_balance = base_balance - total_profit
        else:
            initial_balance = self.df.get('balance_inicial', [10000])[0] if 'balance_inicial' in self.df.columns else 10000

        return {
            "dates": self.df['close_time'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist(),
            "equity": (self.df['cumulative_profit'] + initial_balance).tolist(),
            "drawdown": self.df['drawdown'].tolist(),
            "cumulative_profit": self.df['cumulative_profit'].tolist()
        }

    def calculate_core_metrics(self) -> dict:
        """
        Calculate core trading performance metrics.

        Returns:
            Dictionary with core metrics
        """
        if self.is_empty:
            return self._empty_core_metrics()

        total_trades = len(self.df)
        winning_trades = len(self.df[self.df['profit_usd'] > 0])
        losing_trades = len(self.df[self.df['profit_usd'] < 0])
        breakeven_trades = len(self.df[self.df['profit_usd'] == 0])

        # Win Rate
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Total Profit/Loss
        total_profit = self.df[self.df['profit_usd'] > 0]['profit_usd'].sum()
        total_loss = abs(self.df[self.df['profit_usd'] < 0]['profit_usd'].sum())
        net_profit = self.df['profit_usd'].sum()

        # Profit Factor — cap at 9999 to avoid float('inf') which breaks JSON serialization
        profit_factor = total_profit / total_loss if total_loss > 0 else 9999 if total_profit > 0 else 0

        # Average win/loss
        avg_win = self.df[self.df['profit_usd'] > 0]['profit_usd'].mean() if winning_trades > 0 else 0
        avg_loss = self.df[self.df['profit_usd'] < 0]['profit_usd'].mean() if losing_trades > 0 else 0

        # Expectancy
        expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss) if total_trades > 0 else 0

        # Largest win/loss
        largest_win = self.df['profit_usd'].max() if total_trades > 0 else 0
        largest_loss = self.df['profit_usd'].min() if total_trades > 0 else 0

        # Recovery Factor
        max_dd = abs(self._calculate_max_drawdown())
        recovery_factor = net_profit / max_dd if max_dd > 0 else 0

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "breakeven_trades": breakeven_trades,
            "win_rate": round(win_rate, 2),
            "total_profit": round(total_profit, 2),
            "total_loss": round(total_loss, 2),
            "net_profit": round(net_profit, 2),
            "profit_factor": round(profit_factor, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "expectancy": round(expectancy, 2),
            "largest_win": round(largest_win, 2),
            "largest_loss": round(largest_loss, 2),
            "recovery_factor": round(recovery_factor, 2)
        }

    def calculate_risk_metrics(self) -> dict:
        """
        Calculate risk-related metrics.

        Returns:
            Dictionary with risk metrics
        """
        if self.is_empty:
            return self._empty_risk_metrics()

        # Max Drawdown (Balance-based)
        max_dd_balance = self._calculate_max_drawdown()

        # Max Drawdown Percentage
        initial_balance = 10000  # Default assumption
        self.df['equity_curve'] = self.df['profit_usd'].cumsum() + initial_balance
        running_max = self.df['equity_curve'].cummax()
        dd_percentage = ((self.df['equity_curve'] - running_max) / running_max * 100)
        max_dd_pct = dd_percentage.min()

        # Sharpe Ratio (annualized)
        sharpe_ratio = self._calculate_sharpe_ratio()

        # Sortino Ratio (annualized)
        sortino_ratio = self._calculate_sortino_ratio()

        # Maximum consecutive wins/losses
        max_consec_wins = self._calculate_max_consecutive(True)
        max_consec_losses = self._calculate_max_consecutive(False)

        # Average trade duration
        if 'open_time' in self.df.columns and 'close_time' in self.df.columns:
            durations = (self.df['close_time'] - self.df['open_time']).dt.total_seconds() / 3600
            avg_duration_hours = durations.mean()
        else:
            avg_duration_hours = 0

        return {
            "max_drawdown_usd": round(abs(max_dd_balance), 2),
            "max_drawdown_pct": round(abs(max_dd_pct), 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "sortino_ratio": round(sortino_ratio, 2),
            "max_consecutive_wins": max_consec_wins,
            "max_consecutive_losses": max_consec_losses,
            "avg_trade_duration_hours": round(avg_duration_hours, 2)
        }

    def calculate_temporal_metrics(self) -> dict:
        """
        Calculate profit by time periods.

        Returns:
            Dictionary with temporal analysis
        """
        if self.is_empty:
            return self._empty_temporal_metrics()

        # Extract time components
        self.df['hour'] = self.df['close_time'].dt.hour
        self.df['day_of_week'] = self.df['close_time'].dt.day_name()
        self.df['month'] = self.df['close_time'].dt.month
        self.df['year_month'] = self.df['close_time'].dt.to_period('M').astype(str)

        # Profit by hour
        hourly = self.df.groupby('hour')['profit_usd'].agg(['sum', 'count', 'mean']).reset_index()
        hourly_data = [
            {
                "hour": int(row['hour']),
                "profit": round(row['sum'], 2),
                "trades": int(row['count']),
                "avg_profit": round(row['mean'], 2)
            }
            for _, row in hourly.iterrows()
        ]

        # Profit by day of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        daily = self.df.groupby('day_of_week')['profit_usd'].agg(['sum', 'count', 'mean']).reset_index()
        daily_data = []
        for day in day_order:
            day_data = daily[daily['day_of_week'] == day]
            if len(day_data) > 0:
                daily_data.append({
                    "day": day,
                    "profit": round(day_data['sum'].values[0], 2),
                    "trades": int(day_data['count'].values[0]),
                    "avg_profit": round(day_data['mean'].values[0], 2)
                })
            else:
                daily_data.append({"day": day, "profit": 0, "trades": 0, "avg_profit": 0})

        # Profit by month
        monthly = self.df.groupby('year_month')['profit_usd'].agg(['sum', 'count', 'mean']).reset_index()
        monthly_data = [
            {
                "month": row['year_month'],
                "profit": round(row['sum'], 2),
                "trades": int(row['count']),
                "avg_profit": round(row['mean'], 2)
            }
            for _, row in monthly.iterrows()
        ]

        # Calendar daily data
        self.df['calendar_date'] = self.df['close_time'].dt.date.astype(str)
        calendar = self.df.groupby('calendar_date')['profit_usd'].agg(['sum', 'count']).reset_index()
        calendar_data = [
            {
                "date": row['calendar_date'],
                "profit": round(row['sum'], 2),
                "trades": int(row['count'])
            }
            for _, row in calendar.iterrows()
        ]

        return {
            "hourly": hourly_data,
            "daily": daily_data,
            "monthly": monthly_data,
            "calendar": calendar_data
        }

    def calculate_strategy_metrics(self) -> list[dict]:
        """
        Calculate metrics grouped by Magic Number (strategy).

        Returns:
            List of dictionaries with strategy metrics
        """
        if self.is_empty:
            return []

        # Handle None magic numbers
        self.df['magic_number'] = self.df['magic_number'].fillna(0)

        strategies = []
        for magic, group in self.df.groupby('magic_number'):
            total_trades = len(group)
            winning_trades = len(group[group['profit_usd'] > 0])
            total_profit = group['profit_usd'].sum()
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            # Calculate profit factor for this strategy
            wins = group[group['profit_usd'] > 0]['profit_usd'].sum()
            losses = abs(group[group['profit_usd'] < 0]['profit_usd'].sum())
            profit_factor = wins / losses if losses > 0 else 9999 if wins > 0 else 0

            strategies.append({
                "magic_number": int(magic),
                "strategy_name": f"Strategy {int(magic)}" if magic != 0 else "Manual/Unknown",
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "win_rate": round(win_rate, 2),
                "total_profit": round(total_profit, 2),
                "profit_factor": round(profit_factor, 2),
                "avg_profit": round(group['profit_usd'].mean(), 2),
                "symbols": group['symbol'].unique().tolist()
            })

        return sorted(strategies, key=lambda x: x['total_profit'], reverse=True)

    def calculate_daily_heatmap(self) -> dict:
        """
        Calculate profit for calendar heatmap visualization.

        Returns:
            Dictionary with date-profit pairs for calendar heatmap
        """
        if self.is_empty:
            return {"data": []}

        # Group by date
        self.df['date'] = self.df['close_time'].dt.date
        daily_profit = self.df.groupby('date')['profit_usd'].sum().reset_index()

        return {
            "data": [
                {
                    "date": row['date'].strftime('%Y-%m-%d'),
                    "profit": round(row['profit_usd'], 2)
                }
                for _, row in daily_profit.iterrows()
            ]
        }

    def calculate_symbol_metrics(self) -> list[dict]:
        """
        Calculate metrics grouped by trading symbol.

        Returns:
            List of dictionaries with symbol metrics
        """
        if self.is_empty:
            return []

        symbols = []
        for symbol, group in self.df.groupby('symbol'):
            total_trades = len(group)
            winning_trades = len(group[group['profit_usd'] > 0])
            total_profit = group['profit_usd'].sum()
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            symbols.append({
                "symbol": symbol,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "win_rate": round(win_rate, 2),
                "total_profit": round(total_profit, 2),
                "avg_profit": round(group['profit_usd'].mean(), 2)
            })

        return sorted(symbols, key=lambda x: x['total_profit'], reverse=True)

    def get_full_report(self) -> dict:
        """
        Generate complete performance report.

        Returns:
            Dictionary with all metrics (all values are JSON-safe Python natives)
        """
        report = {
            "core": self.calculate_core_metrics(),
            "risk": self.calculate_risk_metrics(),
            "temporal": self.calculate_temporal_metrics(),
            "strategies": self.calculate_strategy_metrics(),
            "equity_curve": self.calculate_equity_curve(),
            "heatmap": self.calculate_daily_heatmap(),
            "symbols": self.calculate_symbol_metrics()
        }
        return self._sanitize(report)

    def _sanitize(self, obj):
        import json
        import re
        
        # Primero convertimos el dict a un string JSON permitiendo NaNs (que generará 'Infinity' y 'NaN')
        # Utilizamos un encoder custom para asegurar que datetime o objetos raros no rompan esto
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                try:
                    import numpy as np
                    import pandas as pd
                    if isinstance(obj, np.integer): return int(obj)
                    if isinstance(obj, np.floating): return float(obj)
                    if isinstance(obj, np.ndarray): return obj.tolist()
                    if pd.isna(obj): return 0
                except ImportError:
                    pass
                try:
                    return super().default(obj)
                except TypeError:
                    return str(obj)

        json_str = json.dumps(obj, cls=NumpyEncoder, allow_nan=True)
        # Ahora reemplazamos los tokens invalidos de JSON
        json_str = json_str.replace('NaN', '0').replace('Infinity', '9999')
        
        # Volver al dict nativo python sin inf/nan
        return json.loads(json_str)


    # Private helper methods

    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from peak."""
        if self.is_empty:
            return 0

        cumulative = self.df['profit_usd'].cumsum()
        running_max = cumulative.cummax()
        drawdown = cumulative - running_max
        return drawdown.min()

    def _calculate_sharpe_ratio(self) -> float:
        """Calculate annualized Sharpe Ratio."""
        if self.is_empty or len(self.df) < 2:
            return 0

        # Daily returns approximation
        self.df['daily_return'] = self.df['profit_usd']
        returns = self.df['profit_usd']

        if returns.std() == 0:
            return 0

        # Annualize (252 trading days)
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
        return sharpe

    def _calculate_sortino_ratio(self) -> float:
        """Calculate annualized Sortino Ratio."""
        if self.is_empty or len(self.df) < 2:
            return 0

        returns = self.df['profit_usd']
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 9999 if returns.mean() > 0 else 0

        # Downside deviation
        downside_std = downside_returns.std()

        # Annualize
        sortino = (returns.mean() / downside_std) * np.sqrt(252)
        return sortino

    def _calculate_max_consecutive(self, is_win: bool) -> int:
        """Calculate maximum consecutive wins or losses."""
        if self.is_empty:
            return 0

        wins = (self.df['profit_usd'] > 0).astype(int)
        if not is_win:
            wins = (self.df['profit_usd'] < 0).astype(int)

        max_streak = current_streak = 0
        for val in wins:
            if val == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    def _empty_core_metrics(self) -> dict:
        """Return empty core metrics structure."""
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "breakeven_trades": 0,
            "win_rate": 0,
            "total_profit": 0,
            "total_loss": 0,
            "net_profit": 0,
            "profit_factor": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "expectancy": 0,
            "largest_win": 0,
            "largest_loss": 0,
            "recovery_factor": 0
        }

    def _empty_risk_metrics(self) -> dict:
        """Return empty risk metrics structure."""
        return {
            "max_drawdown_usd": 0,
            "max_drawdown_pct": 0,
            "sharpe_ratio": 0,
            "sortino_ratio": 0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
            "avg_trade_duration_hours": 0
        }

    def _empty_temporal_metrics(self) -> dict:
        """Return empty temporal metrics structure."""
        return {
            "hourly": [],
            "daily": [],
            "monthly": [],
            "calendar": []
        }