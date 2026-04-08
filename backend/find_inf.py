import sys, json, math, asyncio
sys.path.insert(0, '.')
from app.database import get_db
from app.routers.metrics import get_trades_for_metrics
from app.services.metrics_engine import MetricsEngine

def find_nan_inf(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            find_nan_inf(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_nan_inf(v, f"{path}[{i}]")
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            print(f"FOUND invalid float at {path}: {obj}")
    else:
        try:
            import numpy as np
            if isinstance(obj, (np.floating, np.integer)) and (np.isnan(obj) or np.isinf(obj)):
                print(f"FOUND invalid numpy value at {path}: {obj} ({type(obj)})")
        except:
            pass

async def main():
    async for db in get_db():
        trades = await get_trades_for_metrics(db, account_id=1, days=30)
        engine = MetricsEngine(trades)
        r = engine.get_full_report()
        find_nan_inf(r)
        
        try:
            json.dumps(r, allow_nan=False)
            print("serialize OK")
        except Exception as e:
            print("JSON serialization error:", e)
        break

if __name__ == "__main__":
    asyncio.run(main())
