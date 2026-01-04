import time
import subprocess
import requests
import yfinance as yf
import pandas as pd

# ======================
# TELEGRAM
# ======================
TELEGRAM_TOKEN = "8245860410:AAFK59QMTb7r5cY4VcJzqFt46tTh4y45ufM"
TELEGRAM_CHAT_ID = "7772237988"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(
        url,
        data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        },
        timeout=10
    )

# ======================
# DATA
# ======================
STOCKS = ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AMD","NFLX","INTC"]

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def scan_market():
    best = None

    for symbol in STOCKS:
        try:
            data = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if len(data) < 60:
                continue

            close = data["Close"]
            price = float(close.iloc[-1])
            rsi = compute_rsi(close).iloc[-1]
            change_30d = ((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100
            ai_score = int((change_30d * 3) + (70 - abs(60 - rsi)) * 2)

            if ai_score >= 70:
                best = {
                    "symbol": symbol,
                    "price": round(price, 2),
                    "target": round(price * 1.10, 2),
                    "stop": round(price * 0.95, 2),
                    "score": ai_score
                }
                break
        except:
            pass

    return best

# ======================
# HLAVNÍ CYKLUS
# ======================
send_telegram("🤖 *Trading bot spuštěn – čekám na signál*")

while True:
    signal = scan_market()

    if signal:
        send_telegram(
            f"""🚀 *BUY SIGNÁL*

📈 Akcie: {signal['symbol']}
💰 Cena: ${signal['price']}
🎯 Cíl: ${signal['target']}
🛑 Stop-loss: ${signal['stop']}
🧠 AI skóre: {signal['score']}

📌 Kup ručně v Trading 212
📌 Nastav LIMIT SELL a STOP-LOSS
"""
        )

        # spustí hlídač ceny
        subprocess.Popen(["python", "price_watcher.py"])

        time.sleep(60 * 60 * 6)  # po signálu pauza 6h

    time.sleep(60 * 15)  # scan každých 15 minut
