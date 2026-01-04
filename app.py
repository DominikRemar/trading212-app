import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
from datetime import datetime, timedelta

# ======================
# TELEGRAM – TVÉ ÚDAJE
# ======================
TELEGRAM_TOKEN = "8245860410:AAFK59QMTb7r5cY4VcJzqFt46tTh4y45ufM"
TELEGRAM_CHAT_ID = "7772237988"

# ======================
# NASTAVENÍ
# ======================
TEST_MODE = st.toggle("🧪 TEST MODE (doporučeno)", value=False)

STOCKS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",
    "META", "TSLA", "AMD", "NFLX", "INTC"
]

RSI_BUY = 50
AI_MIN = 70

# ======================
# TOOLS
# ======================
def trading212_link(symbol):
    return f"https://www.trading212.com/trading-instruments/instrument-details?instrumentId={symbol}"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    })

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ======================
# REAL SCAN
# ======================
def scan_market():
    results = []

    for symbol in STOCKS:
        try:
            data = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if len(data) < 50:
                continue

            close = data["Close"]
            rsi = compute_rsi(close).iloc[-1]
            price = close.iloc[-1]

            ai_score = int(
                (100 - abs(50 - rsi)) +
                (price / close.mean()) * 10
            )

            if rsi < RSI_BUY and ai_score >= AI_MIN:
                results.append({
                    "Akcie": symbol,
                    "Cena ($)": round(price, 2),
                    "RSI": round(rsi, 1),
                    "AI skóre": ai_score,
                    "Signál": "KUPIT",
                    "Prodat při ($)": round(price * 1.12, 2)
                })
        except:
            pass

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    return df.sort_values("AI skóre", ascending=False).head(1)

# ======================
# STREAMLIT UI
# ======================
st.set_page_config(page_title="Trading 212 – AI Polo-automat")
st.title("📈 Trading 212 – AI Polo-automat")
st.warning("⚠️ Není investiční doporučení")

if st.button("🚀 Skenovat trh"):
    if TEST_MODE:
        df = pd.DataFrame([{
            "Akcie": "AAPL",
            "Cena ($)": 190,
            "RSI": 42,
            "AI skóre": 82,
            "Signál": "KUPIT",
            "Prodat při ($)": 215
        }])
        st.success("TEST MODE – vždy 1 akcie")
    else:
        df = scan_market()

    if df.empty:
        st.error("❌ Dnes žádná silná akcie – SAFE režim")
        send_telegram("❌ Dnes žádná silná akcie – SAFE režim")
    else:
        stock = df.iloc[0]
        link = trading212_link(stock["Akcie"])

        msg = f"""
📊 *Trading212 AI – BUY SIGNÁL*

📈 Akcie: {stock['Akcie']}
💰 Cena: ${stock['Cena ($)']}
📉 RSI: {stock['RSI']}
🧠 AI skóre: {stock['AI skóre']}
✅ Signál: KUPIT

🎯 Cíl: ${stock['Prodat při ($)']}

👉 [📈 Otevřít v Trading 212]({link})
"""
        send_telegram(msg)

        st.success("✅ Nalezena silná akcie")
        st.dataframe(df, use_container_width=True)
        st.markdown(f"👉 **[Otevřít v Trading 212]({link})**")
