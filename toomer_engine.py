import requests
import sqlite3
from datetime import datetime

DB_PATH = "toomer_real_paper.db"
STARTING_BALANCE = 100.0
MAX_RISK_PER_TRADE = 0.02
TAKER_FEE_PCT = 0.00075

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
        res = requests.get(url, timeout=5).json()
        return float(res["price"])
    except Exception as e:
        print(f"Data feed error: {e}")
        return None

if __name__ == "__main__":
    init_db()
    price = get_real_price("BTCUSDT")
    print(f"Live Real BTC/USDT Price: ${price}")
