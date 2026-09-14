import sqlite3
import numpy as np

DB_PATH = "toomer_real_paper.db"

def get_learning_multiplier():
    """Calculates dynamic sizing based on win-rate learning from past trades"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT net_pnl FROM trades WHERE status = 'CLOSED' ORDER BY id DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()

    if not rows or len(rows) < 3:
        return 1.0  # Base multiplier

    pnls = [r[0] for r in rows]
    wins = [p for p in pnls if p > 0]
    win_rate = len(wins) / len(pnls)

    # Self-learning adaptive sizing
    if win_rate >= 0.70:
        multiplier = 2.5  # High confidence: Aggressive allocation
    elif win_rate >= 0.50:
        multiplier = 1.5  # Moderate confidence
    else:
        multiplier = 0.8  # Defensive mode: Reduce exposure after drawdowns

    return round(multiplier, 2)

def calculate_aggressive_size(balance, confluence_score, entry, sl):
    """Allocates bigger capital on high-scoring setups"""
    learning_mult = get_learning_multiplier()
    
    # Base risk starts from 4% up to 8% depending on edge
    base_risk_pct = 0.04
    if confluence_score >= 85:
        base_risk_pct = 0.08  # High Potential Shot

    effective_risk_pct = min(base_risk_pct * learning_mult, 0.12) # Cap at 12% max risk
    risk_dollars = balance * effective_risk_pct
    sl_distance = abs(entry - sl)
    
    if sl_distance == 0:
        return 0.0, 0.0

    qty = risk_dollars / sl_distance
    cost = qty * entry

    # Max margin limit: Don't exceed available capital
    if cost > balance:
        cost = balance * 0.95
        qty = cost / entry

    return round(qty, 4), round(cost, 2), round(effective_risk_pct * 100, 1)

if __name__ == "__main__":
    qty, cost, risk = calculate_aggressive_size(1000.0, 90, 77000, 76500)
    print(f"Aggressive Allocation: Cost=${cost} | Size={qty} | Risk={risk}%")
