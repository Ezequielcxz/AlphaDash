"""
Direct MT5 connector test - bypass FastAPI to see raw errors.
Run: python direct_mt5_test.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import MetaTrader5 as mt5
import psutil
import json
from datetime import datetime, timedelta

def find_terminals():
    terminals = []
    seen = set()
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            pname = (proc.info.get('name') or '').lower()
            pexe  = proc.info.get('exe') or ''
            if pname in ('terminal64.exe', 'terminal.exe') and 'windowsapps' not in pexe.lower():
                if pexe not in seen:
                    seen.add(pexe)
                    folder = os.path.basename(os.path.dirname(pexe))
                    terminals.append({'name': folder, 'path': pexe, 'pid': proc.info['pid']})
        except Exception:
            pass
    return terminals

print("=" * 60)
print("MT5 DIRECT CONNECTION TEST")
print("=" * 60)

terminals = find_terminals()
print(f"\nFound {len(terminals)} MT5 terminal(s):")
for t in terminals:
    print(f"  [{t['pid']}] {t['name']}")
    print(f"         {t['path']}")

# Pick Vantage terminal
vantage = next((t for t in terminals if 'vantage' in t['name'].lower()), None)
if not vantage:
    vantage = terminals[0] if terminals else None

if not vantage:
    print("\nERROR: No MT5 terminal detected!")
    sys.exit(1)

print(f"\nTesting with: {vantage['name']}")
print(f"Path: {vantage['path']}")

# Shutdown any existing connection
mt5.shutdown()

print("\n--- Step 1: initialize() ---")
result = mt5.initialize(
    vantage['path'],
    timeout=30000
)
print(f"initialize() result: {result}")
if not result:
    print(f"last_error(): {mt5.last_error()}")
    sys.exit(1)

print("\n--- Step 2: terminal_info() ---")
info = mt5.terminal_info()
if info:
    print(f"  Terminal: {info.name}")
    print(f"  Connected: {info.connected}")
    print(f"  Company: {info.company}")
else:
    print(f"  ERROR: {mt5.last_error()}")

print("\n--- Step 3: account_info() - current logged-in account ---")
acct = mt5.account_info()
if acct:
    print(f"  Login: {acct.login}")
    print(f"  Server: {acct.server}")
    print(f"  Balance: {acct.balance}")
    print(f"  Company: {acct.company}")
else:
    print(f"  ERROR: {mt5.last_error()}")

print("\n--- Step 4: history_deals_get() - last 365 days ---")
from_date = datetime.now() - timedelta(days=365)
to_date = datetime.now()
deals = mt5.history_deals_get(from_date, to_date)
if deals is None:
    print(f"  ERROR: {mt5.last_error()}")
else:
    print(f"  Total deals: {len(deals)}")
    out_deals = [d for d in deals if d.entry in (mt5.DEAL_ENTRY_OUT, mt5.DEAL_ENTRY_OUT_BY)]
    non_balance = [d for d in out_deals if d.type not in (mt5.DEAL_TYPE_BALANCE, mt5.DEAL_TYPE_CREDIT)]
    print(f"  DEAL_ENTRY_OUT deals: {len(out_deals)}")
    print(f"  After balance filter: {len(non_balance)} (these are importable trades)")
    
    if len(deals) > 0 and len(out_deals) == 0:
        print("\n  DIAGNOSIS: MT5 has deals but NONE are DEAL_ENTRY_OUT!")
        print("  Deal entry types found:")
        from collections import Counter
        entry_types = Counter(d.entry for d in deals)
        entry_names = {
            mt5.DEAL_ENTRY_IN: 'DEAL_ENTRY_IN (open)',
            mt5.DEAL_ENTRY_OUT: 'DEAL_ENTRY_OUT (close)',
            mt5.DEAL_ENTRY_INOUT: 'DEAL_ENTRY_INOUT (reverse)',
            mt5.DEAL_ENTRY_OUT_BY: 'DEAL_ENTRY_OUT_BY (close by)',
        }
        for entry, count in entry_types.items():
            name = entry_names.get(entry, f'UNKNOWN({entry})')
            print(f"    {name}: {count}")
    
    if non_balance:
        print(f"\n  First importable trade:")
        d = non_balance[0]
        print(f"    Symbol: {d.symbol}")
        print(f"    Profit: {d.profit}")
        print(f"    Time: {datetime.fromtimestamp(d.time)}")

mt5.shutdown()
print("\n--- Done ---")
