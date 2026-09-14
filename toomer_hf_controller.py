import time
import sqlite3
import toomer_master_brain as brain
import toomer_autonomous as core

DB_PATH = "toomer_real_paper.db"

def is_engine_active():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT engine_status FROM bot_settings WHERE id = 1")
        row = c.fetchone()
        conn.close()
        return row and row[0] == "RUNNING"
    except Exception:
        return False

def run_loop():
    core.init_db()
    print("⚡ [TOOMER MASTER CLOUD CONTROLLER] Online...")
    symbols = ["BTCUSDT", "SOLUSDT"]

    while True:
        try:
            if not is_engine_active():
                print("\r⏸️ [ENGINE PAUSED FROM PHONE ADMIN] Sleeping...", end="", flush=True)
                time.sleep(3)
                continue

            core.monitor_trades()

            for sym in symbols:
                res = brain.calculate_master_confluence(sym)
                if not res:
                    continue

                if res["decision"] in ["BUY", "SELL"]:
                    notes = f"Master Edge: {res['reasons']} | Score: {res['score']}"
                    core.execute_order(sym, res["decision"], res["price"], res["sl"], res["tp"], notes)
                else:
                    print(f"\r🟢 [{sym}] ${res['price']} | Buyers: {res['buyer_ratio']}% | Scan: {res['reasons']}", end="", flush=True)

            time.sleep(1)
        except KeyboardInterrupt:
            break
        except Exception:
            time.sleep(1)

if __name__ == "__main__":
    run_loop()
