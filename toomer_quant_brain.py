import requests
import numpy as np

def fetch_candle_data(symbol="BTCUSDT", interval="15m", limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        res = requests.get(url, timeout=5).json()
        highs = np.array([float(k[2]) for k in res])
        lows = np.array([float(k[3]) for k in res])
        closes = np.array([float(k[4]) for k in res])
        volumes = np.array([float(k[5]) for k in res])
        return highs, lows, closes, volumes
    except Exception:
        return None, None, None, None

def analyze_patterns(symbol="BTCUSDT"):
    highs, lows, closes, volumes = fetch_candle_data(symbol)
    if closes is None or len(closes) < 30:
        return None

    current_price = closes[-1]
    
    # 1. Key Levels: Support & Resistance Detection (Swing Highs & Lows)
    swing_high = np.max(highs[-20:-1])
    swing_low = np.min(lows[-20:-1])
    
    # 2. Volume Spike Analysis
    avg_vol = np.mean(volumes[-20:-1])
    current_vol = volumes[-1]
    vol_spike = current_vol > (avg_vol * 1.4)

    # 3. Trend Analysis via EMAs
    def ema(data, period):
        k = 2 / (period + 1)
        res = [data[0]]
        for val in data[1:]:
            res.append(val * k + res[-1] * (1 - k))
        return res[-1]

    ema_20 = ema(closes, 20)
    ema_50 = ema(closes, 50)

    # 4. Confluence Scoring & Method Testing
    score = 0
    pattern_detected = []

    # Pattern A: Resistance Breakout + Volume Spike (Bullish Breakout)
    if current_price > swing_high and vol_spike:
        score += 40
        pattern_detected.append("Swing Resistance Breakout")
    
    # Pattern B: Support Bounce + EMA Trend Alignment
    elif abs(current_price - swing_low) / current_price < 0.005 and current_price > ema_20:
        score += 35
        pattern_detected.append("Support Level Tap & Rejection")

    # Pattern C: Trend Continuation
    if current_price > ema_20 > ema_50:
        score += 30
        pattern_detected.append("Multi-EMA Trend Alignment")
    elif current_price < ema_20 < ema_50:
        score -= 30
        pattern_detected.append("Bearish Down-Channel")

    # Final Decision
    decision = "HOLD"
    sl = 0.0
    tp = 0.0

    if score >= 65:
        decision = "BUY"
        sl = round(swing_low * 0.996, 2)  # Stop loss just below key swing low
        risk = current_price - sl
        tp = round(current_price + (risk * 2.5), 2)  # 1:2.5 RRR
    elif score <= -65:
        decision = "SELL"
        sl = round(swing_high * 1.004, 2)  # Stop loss above key swing high
        risk = sl - current_price
        tp = round(current_price - (risk * 2.5), 2)

    return {
        "symbol": symbol,
        "decision": decision,
        "confluence_score": score,
        "patterns": ", ".join(pattern_detected) if pattern_detected else "Consolidation / Chop",
        "current_price": current_price,
        "support": swing_low,
        "resistance": swing_high,
        "sl": sl,
        "tp": tp
    }

if __name__ == "__main__":
    report = analyze_patterns("BTCUSDT")
    print("\n--- TOOMER QUANT PATTERN REPORT ---")
    for k, v in report.items():
        print(f"{k}: {v}")
