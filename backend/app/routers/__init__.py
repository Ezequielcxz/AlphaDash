"""Routers package."""
from app.routers.ingest import router as ingest_router
from app.routers.accounts import router as accounts_router
from app.routers.trades import router as trades_router
from app.routers.metrics import router as metrics_router
from app.routers.sync import router as sync_router

__all__ = ["ingest_router", "accounts_router", "trades_router", "metrics_router", "sync_router"]