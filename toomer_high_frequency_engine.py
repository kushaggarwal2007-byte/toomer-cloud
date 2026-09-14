import time
import toomer_master_brain as brain
import toomer_autonomous as core

def run_1sec_loop():
    core.init_db()
    print("⚡ [TOOMER MASTER QUANT ACTIVE] Scanning tick-by-tick every second...")
    
    symbols = ["BTCUSDT", "SOLUSDT"]
    
    while True:
        try:
            # 1. Monitor open positions continuously
            core.monitor_trades()

            # 2. Fast Scan across symbols
            for sym in symbols:
                res = brain.calculate_master_confluence(sym)
                if not res:
                    continue

                if res["decision"] in ["BUY", "SELL"]:
                    notes = f"Master Edge: {res['reasons']} | Score: {res['score']}"
                    core.execute_order(sym, res["decision"], res["price"], res["sl"], res["tp"], notes)
                else:
                    print(f"\r🔍 [{sym}] P: ${res['price']} | RSI: {res['rsi']} | Buyer%: {res['buyer_ratio']}% | Scan Status: {res['reasons']}", end="", flush=True)

            time.sleep(1) # Har 1 second mein continuous deep analysis
        except KeyboardInterrupt:
            print("\nEngine paused.")
            break
        except Exception:
            time.sleep(1)

if __name__ == "__main__":
    run_1sec_loop()
