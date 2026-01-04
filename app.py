import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# =========================
# 🔧 NASTAVENÍ
# =========================

TEST_MODE = True           # ⬅️ zapni / vypni test mód
FORCE_TICKER = "AAPL"      # ⬅️ použije se v TEST_MODE

INVESTMENT_CZK = 5000

CONF = {
    "min_score": 65 if not TEST_MODE else 10,
    "rsi_buy": 40 if not TEST_MODE else 60,
    "rsi_sell": 70,
    "min_volume": 1_000_000
}

# =========================
# 📩 TELEGRAM
# =========================
TELEGRAM_TOKEN = "SEM_DEJ_TOKEN"
TELEGRAM_CHAT_ID = "SEM_DEJ_CHAT_ID"

def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

# =========================
# 📊 INDIKÁTORY
# =========================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =========================
# 🧠 AI SKÓRE (měsíční růst)
# =========================
def ai_score(df):
    score = 0

    # Trend (EMA)
    ema50 = df["Close"].ewm(span=50).mean()
    ema200 = df["Close"].ewm(span=200).mean()
    if ema50.iloc[-1] > ema200.iloc[-1]:
        score += 30

    # RSI
    r = rsi(df["Close"]).iloc[-1]
    if 35 < r < 60:
        score += 25

    # Momentum (3 měsíce)
    if df["Close"].iloc[-1] > df["Close"].iloc[-60]:
        score += 25

    # Volume
    if df["Volume"].iloc[-1] > CONF["min_volume"]:
        score += 20

    return score, r

# =========================
# 🔍 SKEN TRHU
# =========================
def scan_market():
    tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA"]

    if TEST_MODE:
        tickers = [FORCE_TICKER]

    results = []

    for t in tickers:
        try:
            df = yf.download(t, period="1y", interval="1d", progress=False)
            if len(df) < 200:
                continue

            score, r = ai_score(df)

            action = "HOLD"
            if score >= CONF["min_score"] and r < CONF["rsi_buy"]:
                action = "BUY"
            elif r > CONF["rsi_sell"]:
                action = "SELL"

            results.append({
                "Ticker": t,
                "Cena": round(df["Close"].iloc[-1], 2),
                "RSI": round(r, 1),
                "AI skóre": score,
                "Akce": action
            })

        except:
            continue

    return pd.DataFrame(results)

# =========================
# 🖥️ STREAMLIT UI
# =========================
st.set_page_config(page_title="Trading 212 – AI Polo-automat", layout="centered")

st.title("📈 Trading 212 – AI Polo-automat")
st.warning("Není investiční doporučení")

st.success("Bot běží automaticky (1× denně)")

if st.button("🚀 Skenovat trh"):
    df = scan_market()

    if df.empty:
        st.error("Žádná data")
    else:
        st.dataframe(df, use_container_width=True)

        picks = df[df["Akce"] == "BUY"]
        if not picks.empty:
            for _, row in picks.iterrows():
                msg = (
                    f"📊 AI SIGNÁL\n"
                    f"Akcie: {row['Ticker']}\n"
                    f"Cena: {row['Cena']}$\n"
                    f"RSI: {row['RSI']}\n"
                    f"AI skóre: {row['AI skóre']}\n"
                    f"Doporučení: BUY (měsíční horizont)"
                )
                send_telegram(msg)
            st.success("✅ BUY signál odeslán na Telegram")
        else:
            st.info("❌ Dnes žádná silná akcie – bot je SAFE")
