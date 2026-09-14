from flask import Flask, render_template_string, request, jsonify
import sqlite3
import requests

app = Flask(__name__)
DB_PATH = "toomer_real_paper.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Toomer Cloud Admin</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'JetBrains Mono', monospace; }
        body { background-color: #080b11; color: #e5e7eb; padding: 16px; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1f2937; padding-bottom: 12px; margin-bottom: 16px; }
        .logo { font-size: 17px; font-weight: 800; color: #10b981; }
        
        .toggle-box { background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: 16px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .switch { position: relative; display: inline-block; width: 60px; height: 32px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #374151; transition: .3s; border-radius: 34px; }
        .slider:before { position: absolute; content: ""; height: 24px; width: 24px; left: 4px; bottom: 4px; background-color: white; transition: .3s; border-radius: 50%; }
        input:checked + .slider { background-color: #10b981; }
        input:checked + .slider:before { transform: translateX(28px); }

        .form-card { background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: 16px; margin-bottom: 16px; }
        .form-title { font-size: 13px; font-weight: 700; margin-bottom: 12px; color: #38bdf8; }
        .input-group { margin-bottom: 12px; }
        .input-group label { display: block; font-size: 11px; text-transform: uppercase; color: #94a3b8; margin-bottom: 4px; }
        .input-group input, select { width: 100%; background: #1e293b; border: 1px solid #334155; padding: 10px; color: #fff; border-radius: 6px; font-size: 12px; }
        
        .btn { width: 100%; padding: 12px; background: #10b981; color: #000; border: none; font-weight: 800; border-radius: 6px; cursor: pointer; font-size: 13px; }
        .btn:active { background: #059669; }
        .stat-banner { font-size: 12px; padding: 10px; border-radius: 6px; background: #111827; margin-bottom: 16px; border: 1px solid #1f2937; text-align: center; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">⚡ TOOMER CLOUD COMMAND</div>
        <div style="font-size: 11px; color: #94a3b8;">CLOUD HOSTED</div>
    </div>

    <div class="toggle-box">
        <div>
            <div style="font-weight: 700; font-size: 14px;">ENGINE POWER</div>
            <div id="status-text" style="font-size: 11px; color: {% if settings.engine_status == 'RUNNING' %}#10b981{% else %}#ef4444{% endif %};">
                STATUS: {{ settings.engine_status }}
            </div>
        </div>
        <label class="switch">
            <input type="checkbox" id="power-toggle" {% if settings.engine_status == 'RUNNING' %}checked{% endif %} onchange="toggleEngine()">
            <span class="slider"></span>
        </label>
    </div>

    <div class="form-card">
        <div class="form-title">🔑 CONNECT EXCHANGE & SIGNALS</div>
        <form action="/save_settings" method="POST">
            <div class="input-group">
                <label>Active Trading Mode</label>
                <select name="active_exchange">
                    <option value="PAPER" {% if settings.active_exchange == 'PAPER' %}selected{% endif %}>Paper Trading (Real Live Data)</option>
                    <option value="COINDCX" {% if settings.active_exchange == 'COINDCX' %}selected{% endif %}>CoinDCX Pro (Real Live Orders)</option>
                </select>
            </div>
            <div class="input-group">
                <label>CoinDCX API Key</label>
                <input type="password" name="coindcx_api_key" value="{{ settings.coindcx_api_key or '' }}" placeholder="Enter API Key">
            </div>
            <div class="input-group">
                <label>CoinDCX API Secret</label>
                <input type="password" name="coindcx_api_secret" value="{{ settings.coindcx_api_secret or '' }}" placeholder="Enter API Secret">
            </div>
            <div class="input-group">
                <label>TradingView Webhook Passphrase</label>
                <input type="text" name="tradingview_secret" value="{{ settings.tradingview_secret or '' }}" placeholder="Set Webhook Password">
            </div>
            <button type="submit" class="btn">SAVE CREDENTIALS</button>
        </form>
    </div>

    <div class="stat-banner">
        Dashboard View: <a href="http://127.0.0.1:5000" style="color: #38bdf8;" target="_blank">Open Charts & Live PnL Desk</a>
    </div>

    <script>
        function toggleEngine() {
            const isChecked = document.getElementById("power-toggle").checked;
            const newStatus = isChecked ? "RUNNING" : "STOPPED";
            
            fetch("/api/toggle_engine", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: newStatus })
            }).then(r => r.json()).then(data => {
                const txt = document.getElementById("status-text");
                txt.innerText = "STATUS: " + data.status;
                txt.style.color = data.status === "RUNNING" ? "#10b981" : "#ef4444";
            });
        }
    </script>
</body>
</html>
"""

@app.route("/admin")
def admin():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM bot_settings WHERE id = 1")
    settings = dict(c.fetchone())
    conn.close()
    return render_template_string(ADMIN_HTML, settings=settings)

@app.route("/api/toggle_engine", methods=["POST"])
def toggle_engine():
    data = request.get_json()
    new_status = data.get("status", "STOPPED")
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE bot_settings SET engine_status = ? WHERE id = 1", (new_status,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": new_status})

@app.route("/save_settings", methods=["POST"])
def save_settings():
    exchange = request.form.get("active_exchange")
    key = request.form.get("coindcx_api_key")
    sec = request.form.get("coindcx_api_secret")
    tv_sec = request.form.get("tradingview_secret")

    conn = get_db()
    c = conn.cursor()
    c.execute("""
    UPDATE bot_settings 
    SET active_exchange = ?, coindcx_api_key = ?, coindcx_api_secret = ?, tradingview_secret = ?
    WHERE id = 1
    """, (exchange, key, sec, tv_sec))
    conn.commit()
    conn.close()
    return "<script>alert('Credentials Updated Successfully!'); window.location.href='/admin';</script>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
