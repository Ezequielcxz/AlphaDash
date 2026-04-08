#!/usr/bin/env python
"""
AlphaDash Backend Runner

Usage:
    python run.py                  # Run in development mode
    python run.py --host 0.0.0.0   # Run with custom host
    python run.py --port 8080      # Run with custom port
    python run.py --prod           # Run in production mode
"""
import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="AlphaDash API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--prod", action="store_true", help="Run in production mode")
    args = parser.parse_args()

    if args.prod:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            workers=4,
            log_level="info"
        )
    else:
        uvicorn.run(
            "app.main:app",
            host=args.host,
            port=args.port,
            reload=True,
            log_level="debug"
        )


if __name__ == "__main__":
    main()