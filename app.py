import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

# =============================
# 🔧 GLOBÁLNÍ NASTAVENÍ
# =============================
TEST_MODE = True            # ⬅️ pro test
FORCE_TICKER = "AAPL"       # ⬅️ testovací akcie

MIN_AI_SCORE = 70 if not TEST_MODE else 1
CAPITAL_CZK = 5000

# =============================
# 📩 TELEGRAM
# =============================
TELEGRAM_TOKEN = "SEM_DEJ_TOKEN"
TELEGRAM_CHAT_ID = "SEM_DEJ_CHAT_ID"

def telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

# =============================
# 📊 RSI
# =============================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    r = 100 - (100 / (1 + rs))
    return r.fillna(50)

# =============================
# 🧠 AI SKÓRE – PROFESIONÁLNÍ LOGIKA
# =============================
def ai_score(df, info):
    score = 0

    close = df["Close"]
    volume = df["Volume"]

    ema50 = close.ewm(span=50).mean()
    ema200 = close.ewm(span=200).mean()

    r = rsi(close).iloc[-1]

    # 📈 Trend
    if ema50.iloc[-1] > ema200.iloc[-1]:
        score += 20

    # 🔄 RSI – ne přepálené
    if 40 < r < 60:
        score += 15

    # 📊 3měsíční růst
    if close.iloc[-1] > close.iloc[-63]:
        score += 15

    # 📦 Objem
    if volume.iloc[-1] > 1_000_000:
        score += 10

    # 💰 Fundamenty
    if info.get("forwardPE", 100) < 30:
        score += 10
    if info.get("profitMargins", 0) > 0.15:
        score += 10
    if info.get("revenueGrowth", 0) > 0:
        score += 10

    # 📅 Earnings
    earnings = info.get("earningsTimestamp")
    if earnings:
        earn_date = datetime.fromtimestamp(earnings)
        if earn_date > datetime.now():
            score += 10

    return score, r

# =============================
# 🔗 Trading 212
# =============================
def t212(ticker):
    return f"https://www.trading212.com/trading/instruments/instrument/{ticker}"

# =============================
# 🔍 SKEN
# =============================
def scan():
    tickers = [
        "AAPL","MSFT","NVDA","GOOGL","META","AMZN",
        "ASML","AMD","TSLA","NFLX"
    ]

    if TEST_MODE:
        tickers = [FORCE_TICKER]

    rows = []

    for t in tickers:
        try:
            df = yf.download(t, period="1y", progress=False)
            if len(df) < 200:
                continue

            info = yf.Ticker(t).info
            score, r = ai_score(df, info)

            action = "HOLD"
            if score >= MIN_AI_SCORE and r < 55:
                action = "BUY"
            if r > 70:
                action = "SELL"

            rows.append({
                "Ticker": t,
                "Cena ($)": round(df["Close"].iloc[-1], 2),
                "RSI": round(r, 1),
                "AI skóre": score,
                "Akce": action,
                "Trading212": t212(t)
            })

        except:
            continue

    return pd.DataFrame(rows)

# =============================
# 🖥️ UI
# =============================
st.set_page_config("Trading 212 – AI Polo-automat", layout="centered")

st.title("📈 Trading 212 – AI Polo-automat")
st.warning("Není investiční doporučení")
st.success("Bot běží automaticky (1× denně)")

if st.button("🚀 Skenovat trh"):
    df = scan()

    if df.empty:
        st.error("Žádná data")
    else:
        st.dataframe(df, use_container_width=True)

        for _, r in df.iterrows():
            if r["Akce"] in ["BUY","SELL"]:
                telegram(
                    f"📊 AI SIGNÁL\n"
                    f"{r['Akce']} – {r['Ticker']}\n"
                    f"Cena: {r['Cena ($)']}$\n"
                    f"RSI: {r['RSI']}\n"
                    f"AI skóre: {r['AI skóre']}\n"
                    f"Trading212:\n{r['Trading212']}"
                )

        if not (df["Akce"] == "BUY").any():
            st.info("❌ Dnes žádná silná akcie – bot je SAFE")
