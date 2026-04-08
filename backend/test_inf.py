import sys
sys.path.insert(0, '.')
import asyncio
from app.db.session import async_session
from app.crud.trades import get_trades_for_metrics
from app.services.metrics_engine import MetricsEngine
import json

async def main():
    async with async_session() as db:
        trades = await get_trades_for_metrics(db, 1, days=30)
        me = MetricsEngine(trades)
        r = me.get_full_report()
        print('DONE calculing report')
        try:
            json.dumps(r, allow_nan=False)
            print('SUCCESS dumping json')
        except Exception as e:
            print(f'ERROR: {e}')
            def check_dict(d, path=""):
                if isinstance(d, dict):
                    for k, v in d.items():
                        check_dict(v, f"{path}.{k}")
                elif isinstance(d, list):
                    for i, v in enumerate(d):
                        check_dict(v, f"{path}[{i}]")
                elif isinstance(d, float):
                    import math
                    if math.isnan(d) or math.isinf(d):
                        print(f"FOUND INF/NAN at {path}: {d}")
            check_dict(r)

if __name__ == "__main__":
    asyncio.run(main())
