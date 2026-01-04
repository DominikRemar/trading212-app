import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os

# =====================
# KONFIGURACE
# =====================
CAPITAL_CZK = 5000
USD_CZK = 23
RSI_BUY = 40

TICKERS = [
    "AAPL", "MSFT", "NVDA", "META", "GOOGL",
    "AMZN", "TSLA", "PLTR", "COIN"
]

# =====================
# TELEGRAM
# =====================
TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT:
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT, "text": msg})

# =====================
# RSI
# =====================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =====================
# SCAN
# =====================
def scan_market():
    best = None
    best_score = -999

    for t in TICKERS:
        df = yf.download(t, period="3mo", interval="1d", progress=False)
        if df.empty or len(df) < 30:
            continue

        df["RSI"] = rsi(df["Close"])
        last = df.iloc[-1]

        if np.isnan(last["RSI"]):
            continue

        trend = last["Close"] > df["Close"].rolling(20).mean().iloc[-1]
        score = (50 - last["RSI"]) + (10 if trend else 0)

        if score > best_score:
            best_score = score
            best = {
                "ticker": t,
                "price_usd": round(last["Close"], 2),
                "price_czk": int(last["Close"] * USD_CZK),
                "rsi": round(last["RSI"], 1),
                "score": int(score)
            }

    return best

# =====================
# UI
# =====================
st.set_page_config(page_title="Trading 212 – AI Polo-automat", layout="centered")
st.title("🤖 Trading 212 – AI Polo-automat")
st.warning("Není investiční doporučení")

st.success("Bot běží automaticky (1× denně)")
if st.button("🚀 Skenovat trh"):
    pick = scan_market()

    if pick is None:
        st.error("Chyba dat – zkus později")
    else:
        kusy = CAPITAL_CZK // pick["price_czk"]

        df = pd.DataFrame([{
            "Akcie": pick["ticker"],
            "Cena ($)": pick["price_usd"],
            "Cena (Kč)": pick["price_czk"],
            "RSI": pick["rsi"],
            "AI skóre": pick["score"],
            "Kusy": kusy,
            "Signál": "KOUPIT" if pick["rsi"] < RSI_BUY else "SLEDOVAT"
        }])

        st.subheader("🔥 Nejlepší akcie dne")
        st.dataframe(df, use_container_width=True)

        msg = (
            f"📊 Trading 212 – signál\n"
            f"Akcie: {pick['ticker']}\n"
            f"Cena: {pick['price_czk']} Kč\n"
            f"RSI: {pick['rsi']}\n"
            f"Kusy: {kusy}\n"
            f"Signál: {'KOUPIT' if pick['rsi'] < RSI_BUY else 'SLEDOVAT'}"
        )
        send_telegram(msg)
