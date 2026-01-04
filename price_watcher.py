import time
import requests
import yfinance as yf

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
# NASTAVENÍ OBCHODU (VYPLNÍŠ JEN JEDNOU)
# ======================
SYMBOL = "AAPL"          # akcie kterou jsi koupil
BUY_PRICE = 190.0        # nákupní cena
TARGET_PRICE = 215.0     # cíl z AI
STOP_LOSS = round(BUY_PRICE * 0.95, 2)  # -5 %

CHECK_EVERY_MIN = 5      # kontrola ceny

# ======================
send_telegram(
    f"""👀 *HLÍDÁNÍ SPUŠTĚNO*

📈 Akcie: {SYMBOL}
💰 Nákup: ${BUY_PRICE}
🎯 Cíl: ${TARGET_PRICE}
🛑 Stop-loss: ${STOP_LOSS}
"""
)

alert_90_sent = False

# ======================
# HLAVNÍ SMYČKA
# ======================
while True:
    try:
        data = yf.download(SYMBOL, period="1d", interval="1m", progress=False)
        price = float(data["Close"].iloc[-1])

        # 🔔 90 % cíle
        if not alert_90_sent and price >= TARGET_PRICE * 0.9:
            send_telegram(
                f"🔔 *{SYMBOL} je blízko cíle*\nAktuální cena: ${price}"
            )
            alert_90_sent = True

        # 🎯 CÍL
        if price >= TARGET_PRICE:
            send_telegram(
                f"🚨 *CÍL DOSAŽEN – PRODAT*\n{SYMBOL} @ ${price}"
            )
            break

        # 🛑 STOP-LOSS
        if price <= STOP_LOSS:
            send_telegram(
                f"🛑 *STOP-LOSS ZASAŽEN*\n{SYMBOL} @ ${price}"
            )
            break

    except:
        pass

    time.sleep(CHECK_EVERY_MIN * 60)
