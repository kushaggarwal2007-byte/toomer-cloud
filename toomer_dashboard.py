from flask import Flask, render_template_string
import sqlite3
import requests

app = Flask(__name__)
DB_PATH = "toomer_real_paper.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_live_price(symbol):
    try:
        res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}", timeout=3).json()
        return float(res["price"])
    except:
        return 0.0

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Toomer AI Trading Desk</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: \x27JetBrains Mono\x27, monospace; }
        body { background-color: #0b0e14; color: #d1d5db; padding: 24px; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1f2937; padding-bottom: 16px; margin-bottom: 24px; }
        .logo { font-size: 20px; font-weight: 800; color: #10b981; }
        .badge { background: #111827; padding: 6px 12px; border-radius: 6px; font-size: 12px; border: 1px solid #374151; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 28px; }
        .card { background: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 18px; }
        .card-label { font-size: 11px; text-transform: uppercase; color: #9ca3af; margin-bottom: 6px; }
        .card-val { font-size: 22px; font-weight: 800; }
        .green { color: #10b981; }
        .red { color: #ef4444; }
        .blue { color: #3b82f6; }
        table { width: 100%; border-collapse: collapse; background: #111827; border-radius: 8px; overflow: hidden; border: 1px solid #1f2937; margin-bottom: 24px; }
        th, td { padding: 12px 16px; text-align: left; font-size: 13px; border-bottom: 1px solid #1f2937; }
        th { background: #161e2e; color: #9ca3af; font-size: 11px; text-transform: uppercase; }
        .tag { padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; }
        .tag-buy { background: rgba(16, 185, 129, 0.15); color: #10b981; }
        .tag-sell { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
        .section-title { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #f3f4f6; }
    </style>
    <script>
        setInterval(() => { location.reload(); }, 5000);
    </script>
</head>
<body>
    <div class="header">
        <div class="logo">⚡ TOOMER QUANT TERMINAL</div>
        <div class="badge">● LIVE REAL-DATA STREAM</div>
    </div>

    <div class="stats-grid">
        <div class="card">
            <div class="card-label">Current Balance</div>
            <div class="card-val green">${{ "%.2f"|format(balance) }}</div>
        </div>
        <div class="card">
            <div class="card-label">Goal Target</div>
            <div class="card-val blue">$10,000.00</div>
        </div>
        <div class="card">
            <div class="card-label">Realized Net PnL</div>
            <div class="card-val {% if total_pnl >= 0 %}green{% else %}red{% endif %}">
                ${{ "%.2f"|format(total_pnl) }}
            </div>
        </div>
        <div class="card">
            <div class="card-label">Total Trades</div>
            <div class="card-val">{{ closed_trades|length }}</div>
        </div>
    </div>

    <div class="section-title">🔴 ACTIVE POSITIONS</div>
    <table>
        <thead>
            <tr>
                <th>Symbol</th>
                <th>Side</th>
                <th>Entry Price</th>
                <th>Live Price</th>
                <th>Stop Loss</th>
                <th>Take Profit</th>
                <th>Quantity</th>
                <th>Unrealized PnL</th>
            </tr>
        </thead>
        <tbody>
            {% if open_trades %}
                {% for t in open_trades %}
                <tr>
                    <td><strong>{{ t.symbol }}</strong></td>
                    <td><span class="tag {% if t.side == \x27BUY\x27 %}tag-buy{% else %}tag-sell{% endif %}">{{ t.side }}</span></td>
                    <td>${{ "%.2f"|format(t.entry_price) }}</td>
                    <td>${{ "%.2f"|format(t.live_price) }}</td>
                    <td class="red">${{ "%.2f"|format(t.stop_loss) }}</td>
                    <td class="green">${{ "%.2f"|format(t.take_profit) }}</td>
                    <td>{{ "%.4f"|format(t.quantity) }}</td>
                    <td class="{% if t.unrealized >= 0 %}green{% else %}red{% endif %}">
                        ${{ "%.2f"|format(t.unrealized) }}
                    </td>
                </tr>
                {% endfor %}
            {% else %}
                <tr><td colspan="8" style="text-align:center; color:#6b7280; padding:20px;">No active trades. Scanning orderbook for confluences...</td></tr>
            {% endif %}
        </tbody>
    </table>

    <div class="section-title">📜 TRADE HISTORY & SELF-LEARNING LOG</div>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Entry</th>
                <th>Exit</th>
                <th>Fee</th>
                <th>Net PnL</th>
                <th>Confluence Notes</th>
                <th>AI Reflection / Lesson</th>
            </tr>
        </thead>
        <tbody>
            {% if closed_trades %}
                {% for t in closed_trades %}
                <tr>
                    <td>#{{ t.id }}</td>
                    <td>{{ t.symbol }}</td>
                    <td><span class="tag {% if t.side == \x27BUY\x27 %}tag-buy{% else %}tag-sell{% endif %}">{{ t.side }}</span></td>
                    <td>${{ "%.2f"|format(t.entry_price) }}</td>
                    <td>${{ "%.2f"|format(t.exit_price) }}</td>
                    <td class="red">-${{ "%.4f"|format(t.entry_fee + t.exit_fee) }}</td>
                    <td class="{% if t.net_pnl >= 0 %}green{% else %}red{% endif %}">
                        ${{ "%.2f"|format(t.net_pnl) }}
                    </td>
                    <td>{{ t.confluence_notes or \x27Technical Setup\x27 }}</td>
                    <td style="color: #93c5fd;">{{ t.lesson_learned or \x27Logged\x27 }}</td>
                </tr>
                {% endfor %}
            {% else %}
                <tr><td colspan="9" style="text-align:center; color:#6b7280; padding:20px;">No closed trades logged yet.</td></tr>
            {% endif %}
        </tbody>
    </table>
</body>
</html>
"""

@app.route("/")
def dashboard():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM account WHERE id = 1")
    row = c.fetchone()
    balance = row["balance"] if row else 100.0

    c.execute("SELECT * FROM trades WHERE status = \x27OPEN\x27")
    raw_open = c.fetchall()
    open_trades = []
    for t in raw_open:
        d = dict(t)
        live = get_live_price(d["symbol"])
        d["live_price"] = live
        if d["side"] == "BUY":
            d["unrealized"] = (live - d["entry_price"]) * d["quantity"]
        else:
            d["unrealized"] = (d["entry_price"] - live) * d["quantity"]
        open_trades.append(d)

    c.execute("SELECT * FROM trades WHERE status = \x27CLOSED\x27 ORDER BY id DESC LIMIT 20")
    closed_trades = [dict(t) for t in c.fetchall()]
    
    c.execute("SELECT SUM(net_pnl) as total FROM trades WHERE status = \x27CLOSED\x27")
    sum_row = c.fetchone()
    total_pnl = sum_row["total"] if (sum_row and sum_row["total"]) else 0.0
    conn.close()

    return render_template_string(HTML, balance=balance, total_pnl=total_pnl, open_trades=open_trades, closed_trades=closed_trades)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
