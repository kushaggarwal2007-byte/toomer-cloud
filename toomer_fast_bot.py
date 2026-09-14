import time
import sqlite3
import concurrent.futures
import requests
from datetime import datetime

DB_PATH = "toomer_real_paper.db"
PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
TAKER_FEE = 0.00075
MAX_DAILY_LOSS = 35.0  # Daily Drawdown Cap: If net daily loss hits $35, engine freezes

def get_engine_state():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT engine_status FROM bot_settings WHERE id = 1")
        row = c.fetchone()
        conn.close()
        return row[0] if row else "RUNNING"
    except Exception:
        return "RUNNING"

def check_daily_guard():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT SUM(net_pnl) FROM trades WHERE status = 'CLOSED' AND date(close_time) = date('now')")
        val = c.fetchone()[0]
        conn.close()
        daily_pnl = val if val else 0.0
        return daily_pnl > -MAX_DAILY_LOSS
    except Exception:
        return True

def evaluate_conservative_setup(symbol):
    if get_engine_state() != "RUNNING" or not check_daily_guard():
        return

    try:
        # 5-minute candle structure for genuine trend confirmation
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=30"
        res = requests.get(url, timeout=2).json()
        closes = [float(x[4]) for x in res]
        highs = [float(x[2]) for x in res]
        lows = [float(x[3]) for x in res]
        volumes = [float(x[5]) for x in res]
        price = closes[-1]

        # 20-period EMA
        k = 2 / (20 + 1)
        ema_20 = closes[0]
        for c_val in closes[1:]:
            ema_20 = c_val * k + ema_20 * (1 - k)

        # Swing resistance/support
        swing_high = max(highs[-15:-1])
        swing_low = min(lows[-15:-1])
        avg_vol = sum(volumes[-10:]) / 10
        vol_spike = volumes[-1] > (avg_vol * 1.4)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM trades WHERE symbol = ? AND status = 'OPEN'", (symbol,))
        if c.fetchone():
            conn.close()
            return

        side = None
        sl, tp = 0.0, 0.0

        # High-probability Trend Breakout + EMA support
        if price > swing_high and price > ema_20 and vol_spike:
            side = "BUY"
            sl = round(price * 0.992, 4)   # 0.8% Stop Loss
            risk = price - sl
            tp = round(price + (risk * 2.0), 4) # 1:2 RRR (1.6% Target)

        elif price < swing_low and price < ema_20 and vol_spike:
            side = "SELL"
            sl = round(price * 1.008, 4)   # 0.8% Stop Loss
            risk = sl - price
            tp = round(price - (risk * 2.0), 4) # 1:2 RRR (1.6% Target)

        if side:
            c.execute("SELECT balance FROM account WHERE id = 1")
            bal = c.fetchone()[0]
            
            # Disciplined risk: Exactly $10 risk per trade
            risk_budget = 10.0
            sl_distance = abs(price - sl)
            qty = round(risk_budget / sl_distance, 4)
            cost = qty * price
            fee = cost * TAKER_FEE

            c.execute("""
            INSERT INTO trades (symbol, side, entry_price, stop_loss, take_profit, quantity, cost_usd, entry_fee, status, confluence_notes, open_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?, ?)
            """, (symbol, side, price, sl, tp, qty, cost, fee, f"Disciplined 5M Breakout (1:2 RRR)", str(datetime.now())))
            conn.commit()
            print(f"🎯 [CONSERVATIVE ORDER EXECUTED] {side} {symbol} @ {price} | Risk: ${risk_budget:.2f} | Target: ${tp}")

        conn.close()
    except Exception:
        pass

def monitor_active_trades():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, symbol, side, entry_price, stop_loss, take_profit, quantity, entry_fee FROM trades WHERE status = 'OPEN'")
        open_trades = c.fetchall()

        for t in open_trades:
            t_id, sym, side, entry, sl, tp, qty, fee = t
            try:
                r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}", timeout=1).json()
                live = float(r["price"])
            except:
                continue

            close = False
            outcome = ""
            if side == "BUY":
                if live <= sl:
                    close, outcome = True, "STOP LOSS HIT"
                elif live >= tp:
                    close, outcome = True, "TARGET ACHIEVED"
            elif side == "SELL":
                if live >= sl:
                    close, outcome = True, "STOP LOSS HIT"
                elif live <= tp:
                    close, outcome = True, "TARGET ACHIEVED"

            if close:
                exit_fee = (qty * live) * TAKER_FEE
                raw_pnl = (live - entry) * qty if side == "BUY" else (entry - live) * qty
                net_pnl = raw_pnl - fee - exit_fee

                c.execute("SELECT balance FROM account WHERE id = 1")
                bal = c.fetchone()[0]
                new_bal = bal + net_pnl

                lesson = "Disciplined profit target captured." if net_pnl > 0 else "Risk controlled within $10 limit."
                c.execute("""
                UPDATE trades SET status = 'CLOSED', exit_price = ?, exit_fee = ?, net_pnl = ?, lesson_learned = ?, close_time = ?
                WHERE id = ?
                """, (live, exit_fee, net_pnl, lesson, str(datetime.now()), t_id))
                c.execute("UPDATE account SET balance = ? WHERE id = 1", (new_bal,))
                conn.commit()
                print(f"📊 [{outcome}] {sym} Closed. Net PnL: ${net_pnl:.2f} | Current Balance: ${new_bal:.2f}")

        conn.close()
    except Exception:
        pass

def run_loop():
    print("🛡️ [TOOMER DISCIPLINED RISK ENGINE RUNNING]")
    print("Rules Active: Max Risk $10/trade | 1:2 RRR Target | 5M Trend Structure")
    while True:
        monitor_active_trades()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(evaluate_conservative_setup, PAIRS)
        time.sleep(2)

if __name__ == "__main__":
    run_loop()
