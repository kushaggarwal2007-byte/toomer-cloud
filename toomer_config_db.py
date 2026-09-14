import sqlite3

DB_PATH = "toomer_real_paper.db"

def init_config():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS bot_settings (
        id INTEGER PRIMARY KEY,
        engine_status TEXT DEFAULT 'STOPPED',
        active_exchange TEXT DEFAULT 'PAPER',
        coindcx_api_key TEXT,
        coindcx_api_secret TEXT,
        tradingview_secret TEXT
    )
    """)
    c.execute("SELECT id FROM bot_settings WHERE id = 1")
    if not c.fetchone():
        c.execute("""
        INSERT INTO bot_settings (id, engine_status, active_exchange)
        VALUES (1, 'RUNNING', 'PAPER')
        """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_config()
    print("Bot Config Database Ready.")
