import sys, traceback
sys.path.insert(0, '.')
import asyncio
from app.database import get_db
from app.routers.metrics import get_trades_for_metrics
from app.services.metrics_engine import MetricsEngine

async def test():
    async for db in get_db():
        for days in [7, 30, 90]:
            try:
                trades = await get_trades_for_metrics(db, account_id=1, days=days)
                print(f'days={days} trades={len(trades)}')
                engine = MetricsEngine(trades)
                r = engine.get_full_report()
                core = r.get('core', {})
                print(f'  OK total_trades={core.get("total_trades")} net_profit={core.get("net_profit")}')
            except Exception as e:
                print(f'  ERROR days={days}:')
                traceback.print_exc()

asyncio.run(test())
