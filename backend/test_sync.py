"""Diagnostic script: test MT5 direct connection and history retrieval."""
import requests
import json

BASE = "http://localhost:8000/api"

# 1. Detect terminals
r = requests.get(f"{BASE}/sync/terminals")
terminals = r.json()
print("=== TERMINALS ===")
for t in terminals:
    print(f"  {t['name']}: {t['path']} (pid={t['pid']})")

# 2. Pick Vantage terminal
vantage_path = None
for t in terminals:
    if "vantage" in t["name"].lower():
        vantage_path = t["path"]
        break
if not vantage_path and terminals:
    vantage_path = terminals[0]["path"]

print(f"\nSelected terminal: {vantage_path}")

# 3. Try sync with 365 days
print("\n=== SYNCING (365 days) ===")
r2 = requests.post(f"{BASE}/sync/history", json={
    "login": 16240376,
    "password": "PLACEHOLDER_REAL_PASSWORD_NOT_NEEDED_ALREADY_CONNECTED",
    "server": "VantageInternational-Live 5",
    "days_back": 365,
    "path": vantage_path
})
print(f"HTTP Status: {r2.status_code}")
data = r2.json()
print(json.dumps(data, indent=2))
