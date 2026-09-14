import requests
import sqlite3
import time
import math
import os
from datetime import datetime

DB_PATH = "toomer_real_paper.db"
STARTING_BALANCE = 100.0
MAX_RISK_PER_TRADE = 0.02  # Max $2 risk on $100
TAKER_FEE_PCT = 0.00075    # 0.075% Binance fee

def speak_alert(msg):
    print(f"\n🎙️ [TOOMER]: {msg}")
    try:
        # Speaker script ko direct call karna
        speaker_script = os.path.expanduser("~/.openclaw/workspace/alpha-quantum-agent/jarvis_speaker.py")
        if os.path.exists(speaker_script):
            import sys
            sys.path.append(os.path.dirname(speaker_script))
            from jarvis_speaker import speak
            speak(msg)
    except Exception as e:
        pass

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
        lesson_learned TEXT,
        open_time TEXT,
        close_time TEXT
    )
    """)
    c.execute("SELECT balance FROM account WHERE id = 1")
    if not c.fetchone():
        c.execute("INSERT INTO account VALUES (1, ?, ?)", (STARTING_BALANCE, STARTING_BALANCE))
    conn.commit()
    conn.close()

def get_klines(symbol="BTCUSDT", interval="15m", limit=35):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        res = requests.get(url, timeout=5).json()
        closes = [float(k[4]) for k in res]
        return closes
    except Exception:
        return []

def calculate_ema(prices, period):
    k = 2 / (period + 1)
    ema = [prices[0]]
    for p in prices[1:]:
        ema.append(p * k + ema[-1] * (1 - k))
    return ema[-1]

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas[-period:]]
    losses = [-d if d < 0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def evaluate_signal(symbol):
    closes = get_klines(symbol)
    if len(closes) < 30:
        return None
    
    current_price = closes[-1]
    ema_9 = calculate_ema(closes, 9)
    ema_21 = calculate_ema(closes, 21)
    rsi = calculate_rsi(closes)

    # Long Setup: EMA9 > EMA21 aur RSI pullback par (40 - 55 zone)
    if ema_9 > ema_21 and 42 <= rsi <= 55:
        sl = current_price * 0.988  # 1.2% Stop Loss
        tp = current_price + (abs(current_price - sl) * 2.5) # 1:2.5 RRR
        return {"action": "BUY", "price": current_price, "sl": sl, "tp": tp, "rsi": rsi}

    # Short Setup: EMA9 < EMA21 aur RSI rejection par (45 - 58 zone)
    elif ema_9 < ema_21 and 45 <= rsi <= 58:
        sl = current_price * 1.012  # 1.2% Stop Loss
        tp = current_price - (abs(current_price - sl) * 2.5) # 1:2.5 RRR
        return {"action": "SELL", "price": current_price, "sl": sl, "tp": tp, "rsi": rsi}

    return None

def execute_order(symbol, side, entry_price, sl, tp, notes):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Active trade check (ek time par ek trade)
    c.execute("SELECT id FROM trades WHERE status = 'OPEN'")
    if c.fetchone():
        conn.close()
        return

    c.execute("SELECT balance FROM account WHERE id = 1")
    balance = c.fetchone()[0]

    risk_dollars = balance * MAX_RISK_PER_TRADE
    sl_dist = abs(entry_price - sl)
    quantity = risk_dollars / sl_dist
    cost = quantity * entry_price
    
    # Max exposure protection: balance ke 2.5x se zyada exposure nahi
    if cost > (balance * 2.5):
        quantity = (balance * 2.5) / entry_price
        cost = quantity * entry_price

    fee = cost * TAKER_FEE_PCT

    c.execute("""
    INSERT INTO trades (symbol, side, entry_price, stop_loss, take_profit, quantity, cost_usd, entry_fee, status, confluence_notes, open_time)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)
    """, (symbol, side, entry_price, sl, tp, quantity, cost, fee, notes, str(datetime.now())))
    conn.commit()
    conn.close()

    speak_alert(f"Yo bhai! {symbol} pe {side} setup mila hai. Entry price {round(entry_price, 2)} dollar par confirm hui hai.")

def monitor_trades():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, symbol, side, entry_price, stop_loss, take_profit, quantity, entry_fee FROM trades WHERE status = 'OPEN'")
    open_trades = c.fetchall()

    for t in open_trades:
        t_id, sym, side, entry, sl, tp, qty, entry_fee = t
        closes = get_klines(sym, limit=2)
        if not closes:
            continue
        live_price = closes[-1]

        closed = False
        outcome = ""
        lesson = ""

        if side == "BUY":
            if live_price <= sl:
                closed = True
                outcome = "LOSS"
                lesson = "Market structure reversed below EMA. Avoid entry near higher resistance."
            elif live_price >= tp:
                closed = True
                outcome = "PROFIT"
                lesson = "Trend continuation target hit with 1:2.5 risk reward."
        elif side == "SELL":
            if live_price >= sl:
                closed = True
                outcome = "LOSS"
                lesson = "Short squeeze triggered stop loss. Monitor overall volume spikes next time."
            elif live_price <= tp:
                closed = True
                outcome = "PROFIT"
                lesson = "Bearish rejection played out cleanly."

        if closed:
            exit_fee = (qty * live_price) * TAKER_FEE_PCT
            raw_pnl = (live_price - entry) * qty if side == "BUY" else (entry - live_price) * qty
            net_pnl = raw_pnl - entry_fee - exit_fee

            c.execute("SELECT balance FROM account WHERE id = 1")
            bal = c.fetchone()[0]
            new_bal = bal + net_pnl

            c.execute("""
            UPDATE trades SET status = 'CLOSED', exit_price = ?, exit_fee = ?, net_pnl = ?, lesson_learned = ?, close_time = ?
            WHERE id = ?
            """, (live_price, exit_fee, net_pnl, lesson, str(datetime.now()), t_id))
            c.execute("UPDATE account SET balance = ? WHERE id = 1", (new_bal,))
            conn.commit()

            msg = f"Trade close ho gaya hai sir. Net outcome {round(net_pnl, 2)} dollars raha. Naya balance {round(new_bal, 2)} dollar hai."
            speak_alert(msg)

    conn.close()

def run_loop():
    init_db()
    print("🚀 [TOOMER ENGINE RUNNING] Live Real-Market Autonomous Scanner Active...")
    watchlist = ["BTCUSDT", "SOLUSDT"]
    
    while True:
        try:
            # 1. Check open trades against live tick
            monitor_trades()

            # 2. Scan watchlist for new setups
            for symbol in watchlist:
                sig = evaluate_signal(symbol)
                if sig:
                    notes = f"EMA Cross + RSI {round(sig['rsi'], 1)}"
                    execute_order(symbol, sig["action"], sig["price"], sig["sl"], sig["tp"], notes)
                    break
            
            time.sleep(15)  # Har 15 second mein scanning aur monitoring loop
        except KeyboardInterrupt:
            print("\nStopping Toomer...")
            break
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    run_loop()
