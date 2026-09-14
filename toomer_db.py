import sqlite3
from datetime import datetime

DB_NAME = "toomer_paper.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Portfolio Balance Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS account (
        id INTEGER PRIMARY KEY,
        balance REAL,
        starting_capital REAL,
        trades_today INTEGER,
        last_trade_date TEXT
    )
    """)
    
    # Trade Records Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS paper_trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        action TEXT,
        entry_price REAL,
        stop_loss REAL,
        take_profit REAL,
        quantity REAL,
        risk_usd REAL,
        status TEXT,
        pnl REAL,
        confluence_notes TEXT,
        openedBilkul, shuru karte hain! 

Aap aaj kya banana chahte hain? 

* **Koi software ya web application** (React, Python, Node.js, etc.)
* **Automation workflow ya script** (n8n, API integration, bot)
* **Video ya content creation project** (scriptwriting, editing structure)
* **Kuchh aur**

Thoda context de dijiye—kis cheez se start karein?
cd ~/toomer-agent
source venv/bin/activate 2>/dev/null || true

cat << 'EOF' > toomer_engine.py
import requests
import sqlite3
import time
from datetime import datetime

DB_PATH = "toomer_real_paper.db"
STARTING_BALANCE = 100.0
MAX_RISK_PER_TRADE = 0.02   # 2% Max Risk ($2 on $100)
TAKER_FEE_PCT = 0.00075     # 0.075% real exchange fee

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS account (
        id INTEGER PRIMARY KEY,
        balance REAL,
        peak_balance REAL
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        side TEXT,
        entry_price REAL,
        stop_loss REAL,
        take_profit REAL,
        quantity REAL,
        cost_usd REAL,
        entry_fee REAL,
        exit_price REAL,
        exit_fee REAL,
        net_pnl REAL,
        status TEXT,
        confluence_notes TEXT,
        open_time TEXT,
        close_time TEXT
    )
    """)
    c.execute("SELECT balance FROM account WHERE id = 1")
    if not c.fetchone():
        c.execute("INSERT INTO account VALUES (1, ?, ?)", (STARTING_BALANCE, STARTING_BALANCE))
    conn.commit()
    conn.close()

def get_real_price(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        res = requests.get(url, timeout=3).json()
        return float(res["price"])
    except Exception as e:
        print(f"Data feed error: {e}")
        return None

def open_paper_order(symbol, side, entry_price, stop_loss, take_profit, notes="Confluence verified"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM account WHERE id = 1")
    current_balance = c.fetchone()[0]

    risk_dollars = current_balance * MAX_RISK_PER_TRADE
    sl_distance = abs(entry_price - stop_loss)
    
    if sl_distance == 0:
        print("Invalid Stop Loss!")
        conn.close()
        return False

    quantity = risk_dollars / sl_distance
    cost_usd = quantity * entry_price
    
    # Capital safety: Ek trade mein balance ke 3x se zyada exposure nahi
    if cost_usd > (current_balance * 3):
        quantity = (current_balance * 3) / entry_price
        cost_usd = quantity * entry_price

    entry_fee = cost_usd * TAKER_FEE_PCT

    c.execute("""
    INSERT INTO trades (symbol, side, entry_price, stop_loss, take_profit, quantity, cost_usd, entry_fee, status, confluence_notes, open_time)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)
    """, (symbol, side, entry_price, stop_loss, take_profit, quantity, cost_usd, entry_fee, notes, str(datetime.now())))
    
    conn.commit()
    conn.close()

    print(f"\n[REAL ORDER FILLED] {side} {quantity:.4f} {symbol} @ ${entry_price:.2f}")
    print(f"Position Cost: ${cost_usd:.2f} | Max Risk (SL): -${risk_dollars:.2f} | Real Fee Deducted: -${entry_fee:.4f}")
    return True

def monitor_open_positions():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, symbol, side, entry_price, stop_loss, take_profit, quantity, cost_usd, entry_fee FROM trades WHERE status = 'OPEN'")
    open_trades = c.fetchall()

    for trade in open_trades:
        t_id, sym, side, entry, sl, tp, qty, cost, entry_fee = trade
        live_price = get_real_price(sym)
        if not live_price:
            continue

        close = False
        exit_reason = ""

        if side == "BUY":
            if live_price <= sl:
                close = True
                exit_reason = "STOP LOSS HIT"
            elif live_price >= tp:
                close = True
                exit_reason = "TARGET HIT"
        elif side == "SELL":
            if live_price >= sl:
                close = True
                exit_reason = "STOP LOSS HIT"
            elif live_price <= tp:
                close = True
                exit_reason = "TARGET HIT"

        if close:
            exit_fee = (qty * live_price) * TAKER_FEE_PCT
            raw_pnl = (live_price - entry) * qty if side == "BUY" else (entry - live_price) * qty
            net_pnl = raw_pnl - entry_fee - exit_fee

            c.execute("SELECT balance FROM account WHERE id = 1")
            bal = c.fetchone()[0]
            new_bal = bal + net_pnl

            c.execute("""
            UPDATE trades SET status = 'CLOSED', exit_price = ?, exit_fee = ?, net_pnl = ?, close_time = ?
            WHERE id = ?
            """, (live_price, exit_fee, net_pnl, str(datetime.now()), t_id))

            c.execute("UPDATE account SET balance = ? WHERE id = 1", (new_bal,))
            conn.commit()

            print(f"\n--- [TRADE CLOSED: {exit_reason}] ---")
            print(f"Exit Price: ${live_price:.2f}")
            print(f"Exchange Fees: -${(entry_fee + exit_fee):.4f}")
            print(f"Net Real PnL: ${net_pnl:.2f}")
            print(f"Updated Wallet Balance: ${new_bal:.2f}")

    conn.close()

if __name__ == "__main__":
    init_db()
    price = get_real_price("BTCUSDT")
    print(f"Live Real BTC/USDT Price: ${price}")
