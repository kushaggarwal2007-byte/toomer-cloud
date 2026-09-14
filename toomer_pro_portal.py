import os
import sqlite3
import requests
import secrets
import concurrent.futures
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)
DB_PATH = "toomer_real_paper.db"
MASTER_PIN = "7788"

PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "XRPUSDT", "BNBUSDT"]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS bot_settings (
        id INTEGER PRIMARY KEY,
        engine_status TEXT DEFAULT 'RUNNING',
        active_exchange TEXT DEFAULT 'PAPER',
        trading_mode TEXT DEFAULT 'AGGRESSIVE',
        risk_per_trade REAL DEFAULT 5.0,
        coindcx_api_key TEXT,
        coindcx_api_secret TEXT
    )
    """)
    c.execute("SELECT id FROM bot_settings WHERE id = 1")
    if not c.fetchone():
        c.execute("INSERT INTO bot_settings (id, engine_status, active_exchange, trading_mode, risk_per_trade) VALUES (1, 'RUNNING', 'PAPER', 'AGGRESSIVE', 5.0)")
    conn.commit()
    conn.close()

def get_multi_prices():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=2).json()
        p_dict = {item['symbol']: float(item['price']) for item in res if item['symbol'] in PAIRS}
        return p_dict
    except:
        return {}

def fast_scan_pair(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=25"
        res = requests.get(url, timeout=1.5).json()
        closes = [float(x[4]) for x in res]
        highs = [float(x[2]) for x in res]
        lows = [float(x[3]) for x in res]
        price = closes[-1]
        
        # 1-min Fast Momentum & Scalp logic
        diff = closes[-1] - closes[-3]
        pct = (diff / closes[-3]) * 100
        
        action = "WAIT"
        sl, tp = 0.0, 0.0
        if pct > 0.12:  # Aggressive Momentum Breakout
            action = "BUY"
            sl = round(price * 0.995, 4)
            tp = round(price * 1.012, 4)
        elif pct < -0.12:  # Aggressive Breakdown Scalp
            action = "SELL"
            sl = round(price * 1.005, 4)
            tp = round(price * 0.988, 4)

        return {"symbol": symbol, "price": price, "action": action, "sl": sl, "tp": tp, "pct": round(pct, 2)}
    except:
        return {"symbol": symbol, "price": 0.0, "action": "ERR", "sl": 0, "tp": 0, "pct": 0}

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Toomer Pro Lock</title>
    <style>
        body { background:#0b0e14; color:#fff; font-family:-apple-system,BlinkMacSystemFont,sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
        .box { background:#141824; padding:32px; border-radius:14px; border:1px solid #232936; text-align:center; width:300px; box-shadow:0 8px 30px rgba(0,0,0,0.5); }
        input { width:100%; box-sizing:border-box; padding:14px; background:#1b2030; border:1px solid #2d3548; color:#fff; border-radius:8px; font-size:18px; text-align:center; margin:16px 0; letter-spacing:6px; outline:none; }
        button { width:100%; padding:14px; background:#2563eb; color:#fff; border:none; font-weight:700; border-radius:8px; cursor:pointer; font-size:15px; }
        button:hover { background:#1d4ed8; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="color:#38bdf8; margin:0 0 6px 0;">⚡ TOOMER PRO</h2>
        <p style="font-size:12px; color:#8892b0; margin:0;">CoinDCX Style Institutional Terminal</p>
        <form method="POST">
            <input type="password" name="pin" placeholder="PIN" autofocus required maxlength="8">
            <button type="submit">UNLOCK TERMINAL</button>
        </form>
    </div>
</body>
</html>
"""

PRO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Toomer CoinDCX Pro Desk</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing:border-box; margin:0; padding:0; font-family:'Inter', sans-serif; }
        body { background:#0b0e14; color:#e2e8f0; padding:12px; }
        
        /* Top Navigation Header */
        .navbar { display:flex; justify-content:space-between; align-items:center; background:#141824; border:1px solid #1e2538; padding:10px 14px; border-radius:10px; margin-bottom:12px; }
        .logo { font-size:16px; font-weight:800; color:#38bdf8; display:flex; align-items:center; gap:6px; }
        .mode-badge { font-size:10px; font-weight:700; background:rgba(239, 68, 68, 0.2); color:#ef4444; padding:3px 8px; border-radius:4px; border:1px solid rgba(239, 68, 68, 0.4); }
        .btn-logout { background:#1e2538; color:#94a3b8; border:none; padding:6px 12px; border-radius:6px; font-size:11px; font-weight:600; cursor:pointer; text-decoration:none; }

        /* Wallet Cards Bar */
        .metrics-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; margin-bottom:12px; }
        .metric-card { background:#141824; border:1px solid #1e2538; border-radius:10px; padding:12px; }
        .m-label { font-size:10px; color:#8892b0; text-transform:uppercase; font-weight:600; margin-bottom:4px; }
        .m-val { font-size:18px; font-weight:800; }
        .green { color:#10b981; }
        .red { color:#ef4444; }
        .blue { color:#38bdf8; }

        /* Quick Engine Controls */
        .ctrl-bar { display:flex; gap:8px; margin-bottom:12px; }
        .btn-toggle { flex:1; padding:12px; border-radius:8px; font-weight:700; font-size:12px; border:none; cursor:pointer; }
        .btn-running { background:#10b981; color:#000; }
        .btn-stopped { background:#ef4444; color:#fff; }
        .btn-panic { background:#dc2626; color:#fff; padding:0 16px; font-weight:700; font-size:11px; border:none; border-radius:8px; cursor:pointer; }

        /* Watchlist Strip (CoinDCX Market View) */
        .section-title { font-size:12px; font-weight:700; color:#8892b0; text-transform:uppercase; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center; }
        .market-table { width:100%; border-collapse:collapse; background:#141824; border:1px solid #1e2538; border-radius:10px; overflow:hidden; margin-bottom:12px; }
        .market-table th { background:#181d2c; color:#8892b0; font-size:10px; text-transform:uppercase; padding:10px; text-align:left; }
        .market-table td { padding:10px; font-size:12px; border-bottom:1px solid #1a2030; }
        .coin-btn { background:none; border:none; color:#38bdf8; font-weight:700; font-size:13px; cursor:pointer; text-decoration:underline; text-align:left; padding:0; }
        .tag-buy { background:rgba(16, 185, 129, 0.15); color:#10b981; padding:2px 6px; border-radius:4px; font-weight:700; font-size:10px; }
        .tag-sell { background:rgba(239, 68, 68, 0.15); color:#ef4444; padding:2px 6px; border-radius:4px; font-weight:700; font-size:10px; }

        /* Modal Chart Box */
        .modal { display:none; position:fixed; z-index:99; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.8); }
        .modal-content { background:#141824; margin:5% auto; width:95%; max-width:850px; height:520px; border-radius:12px; border:1px solid #232936; overflow:hidden; position:relative; }
        .modal-close { position:absolute; top:8px; right:12px; color:#fff; font-size:24px; font-weight:800; cursor:pointer; z-index:100; }

        /* Form Config */
        .config-card { background:#141824; border:1px solid #1e2538; border-radius:10px; padding:14px; margin-top:12px; }
        .input-row { margin-bottom:10px; }
        .input-row label { display:block; font-size:10px; color:#8892b0; font-weight:600; text-transform:uppercase; margin-bottom:4px; }
        .input-row select, .input-row input { width:100%; background:#1b2030; border:1px solid #2d3548; color:#fff; padding:10px; border-radius:6px; font-size:12px; outline:none; }
        .btn-save { width:100%; background:#2563eb; color:#fff; border:none; padding:11px; font-weight:700; border-radius:6px; cursor:pointer; font-size:12px; }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">⚡ TOOMER COINDCX PRO <span class="mode-badge">⚡ AGGRESSIVE SCALP</span></div>
        <a href="/logout" class="btn-logout">EXIT</a>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="m-label">Portfolio Balance</div>
            <div class="m-val green">${{ "%.2f"|format(balance) }}</div>
        </div>
        <div class="metric-card">
            <div class="m-label">Net PnL</div>
            <div class="m-val {% if total_pnl >= 0 %}green{% else %}red{% endif %}">${{ "%.2f"|format(total_pnl) }}</div>
        </div>
        <div class="metric-card">
            <div class="m-label">Target Milestone</div>
            <div class="m-val blue">$10K</div>
        </div>
    </div>

    <div class="ctrl-bar">
        <button onclick="toggleBot()" id="btn-toggle" class="btn-toggle {% if settings.engine_status == 'RUNNING' %}btn-running{% else %}btn-stopped{% endif %}">
            ENGINE STATUS: {{ settings.engine_status }} (CLICK TO TOGGLE)
        </button>
        <button onclick="panicClose()" class="btn-panic">PANIC EXIT ALL</button>
    </div>

    <div class="section-title">
        <span>⚡ Multi-Pair Market Radar (Click symbol for live chart)</span>
        <span style="font-size:10px; color:#38bdf8;">Auto-refreshing</span>
    </div>
    <table class="market-table">
        <thead>
            <tr>
                <th>Symbol</th>
                <th>Price</th>
                <th>1m Change</th>
                <th>AI Scalp Action</th>
            </tr>
        </thead>
        <tbody id="market-body">
            {% for p in market_data %}
            <tr>
                <td><button class="coin-btn" onclick="openChart('{{ p.symbol }}')">{{ p.symbol }}</button></td>
                <td>${{ "%.4f"|format(p.price) if p.price < 10 else "%.2f"|format(p.price) }}</td>
                <td class="{% if p.pct >= 0 %}green{% else %}red{% endif %}">{{ p.pct }}%</td>
                <td><span class="{% if p.action == 'BUY' %}tag-buy{% elif p.action == 'SELL' %}tag-sell{% endif %}">{{ p.action }}</span></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="section-title">
        <span>🔴 Real Active Executions</span>
    </div>
    <table class="market-table">
        <thead>
            <tr>
                <th>Coin</th>
                <th>Side</th>
                <th>Entry</th>
                <th>Current</th>
                <th>SL</th>
                <th>TP</th>
                <th>Live PnL</th>
            </tr>
        </thead>
        <tbody>
            {% if open_trades %}
                {% for t in open_trades %}
                <tr>
                    <td><button class="coin-btn" onclick="openChart('{{ t.symbol }}')">{{ t.symbol }}</button></td>
                    <td><span class="{% if t.side == 'BUY' %}tag-buy{% else %}tag-sell{% endif %}">{{ t.side }}</span></td>
                    <td>${{ "%.2f"|format(t.entry_price) }}</td>
                    <td>${{ "%.2f"|format(t.live_price) }}</td>
                    <td class="red">${{ "%.2f"|format(t.stop_loss) }}</td>
                    <td class="green">${{ "%.2f"|format(t.take_profit) }}</td>
                    <td class="{% if t.unrealized >= 0 %}green{% else %}red{% endif %}">${{ "%.2f"|format(t.unrealized) }}</td>
                </tr>
                {% endfor %}
            {% else %}
                <tr><td colspan="7" style="text-align:center; color:#64748b; padding:16px;">Scanning 6 pairs aggressively for scalp breakout entries...</td></tr>
            {% endif %}
        </tbody>
    </table>

    <!-- Modal Popup for TradingView Chart on click -->
    <div id="chartModal" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeChart()">&times;</span>
            <div id="tv_chart_container" style="height:100%; width:100%;"></div>
        </div>
    </div>

    <!-- Configuration Settings -->
    <div class="config-card">
        <div style="font-size:12px; font-weight:700; color:#38bdf8; margin-bottom:10px;">⚙️ COINDCX & RISK ROUTING</div>
        <form action="/save_settings" method="POST">
            <div class="input-row">
                <label>Routing Account</label>
                <select name="active_exchange">
                    <option value="PAPER" {% if settings.active_exchange == 'PAPER' %}selected{% endif %}>Paper Scalp Mode (Real Binance Ticks)</option>
                    <option value="COINDCX" {% if settings.active_exchange == 'COINDCX' %}selected{% endif %}>CoinDCX Real Account</option>
                </select>
            </div>
            <div class="input-row">
                <label>Risk Per Trade (Aggressive)</label>
                <input type="number" step="0.5" name="risk_per_trade" value="{{ settings.risk_per_trade or 5.0 }}">
            </div>
            <div class="input-row">
                <label>CoinDCX API Key</label>
                <input type="password" name="coindcx_api_key" value="{{ settings.coindcx_api_key or '' }}">
            </div>
            <div class="input-row">
                <label>CoinDCX API Secret</label>
                <input type="password" name="coindcx_api_secret" value="{{ settings.coindcx_api_secret or '' }}">
            </div>
            <button type="submit" class="btn-save">APPLY AGGRESSIVE SETTINGS</button>
        </form>
    </div>

    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
    <script>
        function openChart(sym) {
            document.getElementById('chartModal').style.display = 'block';
            new TradingView.widget({
                "autosize": true,
                "symbol": "BINANCE:" + sym,
                "interval": "1",
                "timezone": "Asia/Kolkata",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#141824",
                "enable_publishing": false,
                "allow_symbol_change": true,
                "container_id": "tv_chart_container"
            });
        }
        function closeChart() {
            document.getElementById('chartModal').style.display = 'none';
        }
        function toggleBot() {
            fetch("/api/toggle", {method:"POST"}).then(r => r.json()).then(d => location.reload());
        }
        function panicClose() {
            if (confirm("Close all trades now?")) {
                fetch("/api/panic_close", {method:"POST"}).then(() => location.reload());
            }
        }
        setInterval(() => {
            if (document.getElementById('chartModal').style.display !== 'block') {
                location.reload();
            }
        }, 4000);
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if not session.get("auth"):
        if request.method == "POST":
            if request.form.get("pin") == MASTER_PIN:
                session["auth"] = True
                return redirect(url_for("index"))
            return render_template_string(LOGIN_HTML)
        return render_template_string(LOGIN_HTML)

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM bot_settings WHERE id = 1")
    settings = dict(c.fetchone())

    c.execute("SELECT balance FROM account WHERE id = 1")
    row = c.fetchone()
    balance = row["balance"] if row else 100.0

    # Multi-threaded fast scan
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        market_data = list(executor.map(fast_scan_pair, PAIRS))

    p_dict = {m["symbol"]: m["price"] for m in market_data}

    c.execute("SELECT * FROM trades WHERE status = 'OPEN'")
    raw_open = c.fetchall()
    open_trades = []
    for t in raw_open:
        d = dict(t)
        live = p_dict.get(d["symbol"], d["entry_price"])
        d["live_price"] = live
        d["unrealized"] = (live - d["entry_price"]) * d["quantity"] if d["side"] == "BUY" else (d["entry_price"] - live) * d["quantity"]
        open_trades.append(d)

    c.execute("SELECT SUM(net_pnl) as total FROM trades WHERE status = 'CLOSED'")
    s = c.fetchone()
    total_pnl = s["total"] if (s and s["total"]) else 0.0
    conn.close()

    return render_template_string(PRO_HTML, settings=settings, balance=balance, total_pnl=total_pnl, open_trades=open_trades, market_data=market_data)

@app.route("/logout")
def logout():
    session.pop("auth", None)
    return redirect(url_for("index"))

@app.route("/api/toggle", methods=["POST"])
def api_toggle():
    if not session.get("auth"):
        return jsonify({"error": "unauthorized"}), 401
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT engine_status FROM bot_settings WHERE id = 1")
    curr = c.fetchone()["engine_status"]
    new_s = "STOPPED" if curr == "RUNNING" else "RUNNING"
    c.execute("UPDATE bot_settings SET engine_status = ? WHERE id = 1", (new_s,))
    conn.commit()
    conn.close()
    return jsonify({"status": new_s})

@app.route("/api/panic_close", methods=["POST"])
def panic_close():
    if not session.get("auth"):
        return jsonify({"error": "unauthorized"}), 401
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE trades SET status = 'CLOSED', close_time = datetime('now') WHERE status = 'OPEN'")
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/save_settings", methods=["POST"])
def save_settings():
    if not session.get("auth"):
        return redirect(url_for("index"))
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    UPDATE bot_settings 
    SET active_exchange = ?, risk_per_trade = ?, coindcx_api_key = ?, coindcx_api_secret = ?
    WHERE id = 1
    """, (request.form.get("active_exchange"), float(request.form.get("risk_per_trade") or 5.0), request.form.get("coindcx_api_key"), request.form.get("coindcx_api_secret")))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080, debug=False)
