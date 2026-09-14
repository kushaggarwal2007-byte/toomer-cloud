import requests
import numpy as np
import time
import math

def get_market_depth_and_candles(symbol="BTCUSDT"):
    """Live 1-sec level micro data fetch"""
    try:
        # 1m candles for immediate micro-trend
        c_url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=40"
        res_c = requests.get(c_url, timeout=2).json()
        closes = np.array([float(k[4]) for k in res_c])
        highs = np.array([float(k[2]) for k in res_c])
        lows = np.array([float(k[3]) for k in res_c])
        volumes = np.array([float(k[5]) for k in res_c])

        # Real-time Orderbook depth for micro psychology
        d_url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=10"
        res_d = requests.get(d_url, timeout=2).json()
        bids = sum([float(b[1]) for b in res_d["bids"]])
        asks = sum([float(a[1]) for a in res_d["asks"]])

        return closes, highs, lows, volumes, bids, asks
    except Exception:
        return None, None, None, None, 0, 0

def calculate_master_confluence(symbol="BTCUSDT"):
    closes, highs, lows, volumes, bids, asks = get_market_depth_and_candles(symbol)
    if closes is None or len(closes) < 30:
        return None

    current_price = closes[-1]
    
    # 1. PSYCHOLOGY & ORDERBOOK PRESSURE
    # Bid/Ask imbalance ratio (Buyer vs Seller dominance)
    total_depth = bids + asks
    buyer_pressure = (bids / total_depth) * 100 if total_depth > 0 else 50.0

    # 2. TECHNICAL INDICATORS (EMA & RSI)
    def calc_ema(arr, period):
        k = 2 / (period + 1)
        val = arr[0]
        for x in arr[1:]:
            val = x * k + val * (1 - k)
        return val

    ema_9 = calc_ema(closes, 9)
    ema_21 = calc_ema(closes, 21)
    
    diffs = np.diff(closes[-15:])
    gains = diffs[diffs > 0]
    losses = -diffs[diffs < 0]
    avg_g = np.mean(gains) if len(gains) > 0 else 0.0001
    avg_l = np.mean(losses) if len(losses) > 0 else 0.0001
    rsi = 100.0 - (100.0 / (1.0 + (avg_g / avg_l)))

    # 3. PATTERN & LIQUIDITY SWEEP
    swing_high = np.max(highs[-20:-1])
    swing_low = np.min(lows[-20:-1])
    vol_mean = np.mean(volumes[-20:-1])
    vol_spike = volumes[-1] > (vol_mean * 1.5)

    # 4. MASTER CONFLUENCE SCORING (Max 100)
    long_score = 0
    short_score = 0
    reasons = []

    # Bullish criteria
    if ema_9 > ema_21:
        long_score += 25
    if 40 <= rsi <= 55:  # Pullback bounce zone
        long_score += 25
        reasons.append("RSI Momentum Support")
    if buyer_pressure > 58: # Institutional bid wall
        long_score += 25
        reasons.append("Orderbook Buyer Wall")
    if current_price > swing_high and vol_spike: # Liquidity breakout
        long_score += 25
        reasons.append("High-Volume Liquidity Breakout")

    # Bearish criteria
    if ema_9 < ema_21:
        short_score += 25
    if 45 <= rsi <= 60:
        short_score += 25
        reasons.append("RSI Rejection")
    if buyer_pressure < 42:
        short_score += 25
        reasons.append("Orderbook Sell Wall Dominance")
    if current_price < swing_low and vol_spike:
        short_score += 25
        reasons.append("Liquidity Breakdown Flush")

    decision = "WAIT"
    final_score = 0
    sl = 0.0
    tp = 0.0

    # Strict entry: Only execute when 75+ confluence matches
    if long_score >= 75:
        decision = "BUY"
        final_score = long_score
        sl = round(swing_low * 0.998, 2)
        risk = max(current_price - sl, current_price * 0.004) # min 0.4% SL
        sl = current_price - risk
        tp = round(current_price + (risk * 2.5), 2) # 1:2.5 RRR
    elif short_score >= 75:
        decision = "SELL"
        final_score = short_score
        sl = round(swing_high * 1.002, 2)
        risk = max(sl - current_price, current_price * 0.004)
        sl = current_price + risk
        tp = round(current_price - (risk * 2.5), 2)

    return {
        "symbol": symbol,
        "price": current_price,
        "decision": decision,
        "score": final_score,
        "buyer_ratio": round(buyer_pressure, 1),
        "rsi": round(rsi, 1),
        "reasons": ", ".join(reasons) if reasons else "No clear edge",
        "sl": sl,
        "tp": tp
    }

if __name__ == "__main__":
    report = calculate_master_confluence("BTCUSDT")
    print("\n--- 1-SECOND QUANT SCAN REPORT ---")
    for k, v in report.items():
        print(f"{k}: {v}")
