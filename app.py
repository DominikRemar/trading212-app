import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os

# ======================
# KONFIGURACE
# ======================
INVEST_KC = 5000
USD_CZK = 23
TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "PLTR", "COIN"]

TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

# ======================
# TELEGRAM
# ======================
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    requests.post(url, data=data)

# ======================
# INDIKÁTORY
# ======================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def ai_score(rsi_val, trend):
    score = 0
    if rsi_val < 30:
        score += 40
    elif rsi_val < 40:
        score += 20
    if trend > 0:
        score += 30
    return min(score, 100)

# ======================
# STREAMLIT UI
# ======================
st.set_page_config(page_title="Trading 212 – AI Polo-automat", layout="centered")

st.title("📈 Trading 212 – AI Polo-automat")
st.warning("⚠️ Není investiční doporučení")

st.success("✅ Připraveno – klikni na Skenovat trh")

if st.button("🚀 Skenovat trh"):
    results = []

    for t in TICKERS:
        try:
            df = yf.download(t, period="6mo", interval="1d", progress=False)
            if df.empty:
                continue

            df["RSI"] = rsi(df["Close"])
            last = df.iloc[-1]

            if pd.isna(last["RSI"]):
                continue

            trend = df["Close"].iloc[-1] - df["Close"].iloc[-20]
            score = ai_score(last["RSI"], trend)

            price_usd = round(last["Close"], 2)
            price_kc = round(price_usd * USD_CZK)
            kusy = int(INVEST_KC / price_kc)

            signal = "KUPIT" if score >= 60 else "SLEDOVAT"

            results.append({
                "Akcie": t,
                "Cena ($)": price_usd,
                "Cena (Kč)": price_kc,
                "RSI": round(last["RSI"], 1),
                "AI skóre": score,
                "Signál": signal,
                "Kusy": kusy
            })
        except:
            continue

    if not results:
        st.error("❌ Nepodařilo se načíst data")
    else:
        df = pd.DataFrame(results).sort_values("AI skóre", ascending=False)

        # VŽDY vybereme alespoň 1 akcii
        best = df.iloc[0]

        st.subheader("🔥 Nejlepší dostupná akcie")
        st.dataframe(pd.DataFrame([best]), use_container_width=True)

        # Telegram jen při KUPIT
        if best["Signál"] == "KUPIT":
            send_telegram(
                f"📈 Trading 212 – AI ALERT\n\n"
                f"Akcie: {best['Akcie']}\n"
                f"Signál: {best['Signál']}\n"
                f"Cena: {best['Cena (Kč)']} Kč\n"
                f"RSI: {best['RSI']}\n"
                f"AI skóre: {best['AI skóre']}\n"
                f"Kusy za {INVEST_KC} Kč: {best['Kusy']}"
            )
