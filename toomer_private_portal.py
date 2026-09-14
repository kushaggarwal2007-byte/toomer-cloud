from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import sqlite3
import requests
import os
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(24)
DB_PATH = "toomer_real_paper.db"

# Master PIN/Password
MASTER_PIN = "7788"

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
        engine_status TEXT DEFAULT \x27RUNNING\x27,
        active_exchange TEXT DEFAULT \x27PAPER\x27,
        risk_per_trade REAL DEFAULT 2.0,
        coindcx_api_key TEXT,
        coindcx_api_secret TEXT,
        tradingview_secret TEXT
    )
    """)
    c.execute("SELECT id FROM bot_settings WHERE id = 1")
    if not c.fetchone():
        c.execute("INSERT INTO bot_settings (id, engine_status, active_exchange, risk_per_trade) VALUES (1, \x27RUNNING\x27, \x27PAPER\x27, 2.0)")
    conn.commit()
    conn.close()

def get_live_price(symbol="BTCUSDT"):
    try:
        res = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}", timeout=2).json()
        return float(res["price"])
    except:
        return 0.0

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Toomer Vault Access</title>
    <style>
        body { background:#080b11; color:#fff; font-family:monospace; display:flex; justify-content:center; align-items:center; height:100vh; margin:0; }
        .box { background:#0f172a; padding:30px; border-radius:12px; border:1px solid #1e293b; text-align:center; width:280px; }
        input { width:100%; padding:12px; background:#1e293b; border:1px solid #334155; color:#fff; border-radius:6px; font-size:16px; text-align:center; margin:16px 0; letter-spacing:4px; }
        button { width:100%; padding:12px; background:#10b981; border:none; font-weight:800; border-radius:6px; cursor:pointer; font-size:14px; }
    </style>
</head>
<body>
    <div class="box">
        <h3 style="color:#10b981; margin:0;">🔒 TOOMER VAULT</h3>
        <p style="font-size:11px; color:#94a3b8; margin-top:6px;">ENTER SECURE ADMIN PIN</p>
        <form method="POST">
            <input type="password" name="pin" placeholder="PIN" autofocus required maxlength="8">
            <button type="submit">UNLOCK TERMINAL</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>⚡ Toomer Private Command</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing:border-box; margin:0; padding:0; font-family:\x27JetBrains Mono\x27, monospace; }
        body { background:#080b11; color:#e5e7eb; padding:14px; }
        .topbar { display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #1e293b; padding-bottom:10px; margin-bottom:14px; }
        .logo { font-size:16px; font-weight:800; color:#10b981; }
        .btn-sm { background:#1e293b; color:#94a3b8; border:1px solid #334155; padding:4px 8px; border-radius:4px; text-decoration:none; font-size:11px; }

        .control-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:14px; }
        .ctrl-card { background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:12px; }
        .ctrl-label { font-size:10px; color:#94a3b8; text-transform:uppercase; margin-bottom:6px; }
        
        /* Master Toggle */
        .switch { position:relative; display:inline-block; width:52px; height:28px; }
        .switch input { opacity:0; width:0; height:0; }
        .slider { position:absolute; cursor:pointer; top:0; left:0; right:0; bottom:0; background-color:#374151; transition:.3s; border-radius:28px; }
        .slider:before { position:absolute; content:\x27\x27; height:20px; width:20px; left:4px; bottom:4px; background-color:white; transition:.3s; border-radius:50%; }
        input:checked + .slider { background-color:#10b981; }
        input:checked + .slider:before { transform:translateX(24px); }

        .stats-strip { display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; margin-bottom:14px; }
        .stat-item { background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:10px; text-align:center; }
        .stat-val { font-size:16px; font-weight:800; margin-top:4px; }
        .green { color:#10b981; }
        .red { color:#ef4444; }
        .blue { color:#38bdf8; }

        .chart-box { height:360px; background:#0f172a; border:1px solid #1e293b; border-radius:8px; overflow:hidden; margin-bottom:14px; }
        
        .section-title { font-size:12px; font-weight:700; margin-bottom:8px; color:#94a3b8; text-transform:uppercase; display:flex; justify-content:space-between; }
        table { width:100%; border-collapse:collapse; background:#0f172a; border-radius:8px; overflow:hidden; border:1px solid #1e293b; margin-bottom:14px; }
        th, td { padding:8px 10px; font-size:11px; text-align:left; border-bottom:1px solid #1e293b; }
        th { background:#1e293b; color:#94a3b8; font-size:9px; text-transform:uppercase; }

        .form-panel { background:#0f172a; border:1px solid #1e293b; border-radius:8px; padding:14px; margin-bottom:14px; }
        .field { margin-bottom:10px; }
        .field label { display:block; font-size:10px; color:#94a3b8; text-transform:uppercase; margin-bottom:4px; }
        .field input, select { width:100%; background:#1e293b; border:1px solid #334155; padding:8px; color:#fff; border-radius:6px; font-size:11px; }
        .save-btn { width:100%; padding:10px; background:#10b981; color:#000; border:none; font-weight:800; border-radius:6px; font-size:12px; cursor:pointer; }
        .kill-btn { width:100%; padding:10px; background:#ef4444; color:#fff; border:none; font-weight:800; border-radius:6px; font-size:11px; cursor:pointer; margin-top:8px; }
    </style>
    <script>
        function toggleBot() {
            const chk = document.getElementById("eng-switch").checked;
            fetch("/api/toggle", {
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({status: chk ? "RUNNING" : "STOPPED"})
            }).then(r => r.json()).then(d => {
                document.getElementById("eng-status").innerText = d.status;
                document.getElementById("eng-status").className = d.status === "RUNNING" ? "green" : "red";
            });
        }
        function panicClose() {
            if (confirm("Close all open positions instantly at market price?")) {
                fetch("/api/panic_close", {method:"POST"}).then(() => location.reload());
            }
        }
    </script>
</head>
<body>
    <div class="topbar">
        <div class="logo">⚡ TOOMER PRIVATE DESK</div>
        <a href="/logout" class="btn-sm">LOGOUT</a>
    </div>

    <div class="control-grid">
        <div class="ctrl-card">
            <div class="ctrl-label">Engine Switch</div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span id="eng-status" class="{% if settings.engine_status == \x27RUNNING\x27 %}green{% else %}red{% endif %}" style="font-weight:800; font-size:12px;">
                    {{ settings.engine_status }}
                </span>
                <label class="switch">
                    <input type="checkbox" id="eng-switch" {% if settings.engine_status == \x27RUNNING\x27 %}checked{% endif %} onchange="toggleBot()">
                    <span class="slider"></span>
                </label>
            </div>
        </div>
        <div class="ctrl-card">
            <div class="ctrl-label">Active Mode</div>
            <div style="font-weight:800; font-size:12px; color:#38bdf8;">{{ settings.active_exchange }}</div>
            <div style="font-size:9px; color:#94a3b8; margin-top:4px;">Risk: {{ settings.risk_per_trade }}% Max</div>
        </div>
    </div>

    <div class="stats-strip">
        <div class="stat-item">
            <div style="font-size:9px; color:#94a3b8;">BALANCE</div>
            <div class="stat-val green">${{ "%.2f"|format(balance) }}</div>
        </div>
        <div class="stat-item">
            <div style="font-size:9px; color:#94a3b8;">TARGET</div>
            <div class="stat-val blue">$10K</div>
        </div>
        <div class="stat-item">
            <div style="font-size:9px; color:#94a3b8;">NET PNL</div>
            <div class="stat-val {% if total_pnl >= 0 %}green{% else %}red{% endif %}">${{ "%.2f"|format(total_pnl) }}</div>
        </div>
    </div>

    <!-- Interactive TradingView Chart -->
    <div class="chart-box">
        <div id="tv_chart" style="height:100%;width:100%"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({
            "autosize": true,
            "symbol": "BINANCE:BTCUSDT",
            "interval": "15",
            "timezone": "Asia/Kolkata",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#0f172a",
            "enable_publishing": false,
            "allow_symbol_change": true,
            "container_id": "tv_chart"
        });
        </script>
    </div>

    <div class="section-title">
        <span>🔴 Active Live Positions</span>
        <button onclick="panicClose()" class="btn-sm" style="color:#ef4444; border-color:#ef4444;">PANIC CLOSE ALL</button>
    </div>
    <table>
        <thead>
            <tr>
                <th>Pair</th>
                <th>Side</th>
                <th>Entry</th>
                <th>Live</th>
                <th>SL</th>
                <th>TP</th>
                <th>PnL</th>
            </tr>
        </thead>
        <tbody>
            {% if open_trades %}
                {% for t in open_trades %}
                <tr>
                    <td><strong>{{ t.symbol }}</strong></td>
                    <td class="{% if t.side == \x27BUY\x27 %}green{% else %}red{% endif %}">{{ t.side }}</td>
                    <td>${{ "%.1f"|format(t.entry_price) }}</td>
                    <td>${{ "%.1f"|format(t.live_price) }}</td>
                    <td class="red">${{ "%.1f"|format(t.stop_loss) }}</td>
                    <td class="green">${{ "%.1f"|format(t.take_profit) }}</td>
                    <td class="{% if t.unrealized >= 0 %}green{% else %}red{% endif %}">${{ "%.2f"|format(t.unrealized) }}</td>
                </tr>
                {% endfor %}
            {% else %}
                <tr><td colspan="7" style="text-align:center; color:#64748b; padding:12px;">Scanning Orderbook Confluences...</td></tr>
            {% endif %}
        </tbody>
    </table>

    <div class="form-panel">
        <div style="font-size:11px; font-weight:800; margin-bottom:10px; color:#38bdf8;">⚙️ INTEGRATIONS & SETTINGS</div>
        <form action="/save_settings" method="POST">
            <div class="field">
                <label>Routing Exchange</label>
                <select name="active_exchange">
                    <option value="PAPER" {% if settings.active_exchange == \x27PAPER\x27 %}selected{% endif %}>Paper Mode (Real Binance Orderbook Tick)</option>
                    <option value="COINDCX" {% if settings.active_exchange == \x27COINDCX\x27 %}selected{% endif %}>CoinDCX Real Live Execution</option>
                </select>
            </div>
            <div class="field">
                <label>Max Risk Per Trade (%)</label>
                <input type="number" step="0.5" name="risk_per_trade" value="{{ settings.risk_per_trade or 2.0 }}">
            </div>
            <div class="field">
                <label>CoinDCX API Key</label>
                <input type="password" name="coindcx_api_key" value="{{ settings.coindcx_api_key or \x27\x27 }}" placeholder="Paste CoinDCX API Key">
            </div>
            <div class="field">
                <label>CoinDCX API Secret</label>
                <input type="password" name="coindcx_api_secret" value="{{ settings.coindcx_api_secret or \x27\x27 }}" placeholder="Paste CoinDCX Secret">
            </div>
            <div class="field">
                <label>TradingView Passphrase</label>
                <input type="text" name="tradingview_secret" value="{{ settings.tradingview_secret or \x27\x27 }}" placeholder="Webhook Secret">
            </div>
            <button type="submit" class="save-btn">UPDATE SYSTEM SETTINGS</button>
        </form>
    </div>
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

    c.execute("SELECT * FROM trades WHERE status = \x27OPEN\x27")
    raw_open = c.fetchall()
    open_trades = []
    for t in raw_open:
        d = dict(t)
        live = get_live_price(d["symbol"])
        d["live_price"] = live
        d["unrealized"] = (live - d["entry_price"]) * d["quantity"] if d["side"] == "BUY" else (d["entry_price"] - live) * d["quantity"]
        open_trades.append(d)

    c.execute("SELECT SUM(net_pnl) as total FROM trades WHERE status = \x27CLOSED\x27")
    s = c.fetchone()
    total_pnl = s["total"] if (s and s["total"]) else 0.0
    conn.close()

    return render_template_string(DASHBOARD_HTML, settings=settings, balance=balance, total_pnl=total_pnl, open_trades=open_trades)

@app.route("/logout")
def logout():
    session.pop("auth", None)
    return redirect(url_for("index"))

@app.route("/api/toggle", methods=["POST"])
def api_toggle():
    if not session.get("auth"):
        return jsonify({"error": "unauthorized"}), 401
    status = request.get_json().get("status", "STOPPED")
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE bot_settings SET engine_status = ? WHERE id = 1", (status,))
    conn.commit()
    conn.close()
    return jsonify({"status": status})

@app.route("/api/panic_close", methods=["POST"])
def panic_close():
    if not session.get("auth"):
        return jsonify({"error": "unauthorized"}), 401
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE trades SET status = \x27CLOSED\x27, close_time = datetime(\x27now\x27) WHERE status = \x27OPEN\x27")
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/save_settings", methods=["POST"])
def save_settings():
    if not session.get("auth"):
        return redirect(url_for("index"))
    exchange = request.form.get("active_exchange")
    risk = float(request.form.get("risk_per_trade") or 2.0)
    key = request.form.get("coindcx_api_key")
    sec = request.form.get("coindcx_api_secret")
    tv = request.form.get("tradingview_secret")

    conn = get_db()
    c = conn.cursor()
    c.execute("""
    UPDATE bot_settings 
    SET active_exchange = ?, risk_per_trade = ?, coindcx_api_key = ?, coindcx_api_secret = ?, tradingview_secret = ?
    WHERE id = 1
    """, (exchange, risk, key, sec, tv))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080, debug=False)
