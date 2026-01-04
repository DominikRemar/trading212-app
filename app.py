import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# =========================
# KONFIGURACE
# =========================
CONF = {
    "tickers": ["AAPL", "MSFT", "NVDA", "META", "GOOGL", "TSLA", "AMZN", "COIN"],
    "rsi_buy": 30,
    "rsi_sell": 70,
    "ai_min_score": 60
}

# =========================
# TELEGRAM
# =========================
def send_telegram(msg):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg})
    except Exception as e:
        st.warning(f"Telegram chyba: {e}")

# =========================
# RSI
# =========================
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# =========================
# SKEN TRHU
# =========================
def scan_market():
    picks = []

    for ticker in CONF["tickers"]:
        try:
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)

            if df.empty or "Close" not in df:
                continue

            df["RSI"] = compute_rsi(df["Close"])
            last = df.iloc[-1]

            # OCHRANA PROTI NaN
            if pd.isna(last["RSI"]):
                continue

            ai_score = int(100 - abs(last["RSI"] - 30))

            if last["RSI"] < CONF["rsi_buy"] and ai_score >= CONF["ai_min_score"]:
                price_usd = float(last["Close"])
                price_czk = price_usd * 23

                picks.append({
                    "Akcie": ticker,
                    "Cena ($)": round(price_usd, 2),
                    "Cena (Kč)": round(price_czk),
                    "RSI": round(last["RSI"], 1),
                    "AI skóre": ai_score,
                    "Signál": "🟢 KOUPIT"
                })

        except Exception:
            continue

    return pd.DataFrame(picks)

# =========================
# STREAMLIT UI
# =========================
st.set_page_config(page_title="Trading 212 – AI Polo-automat", layout="centered")

st.title("🤖 Trading 212 – AI Polo-automat")
st.warning("⚠️ Není investiční doporučení")

st.success("✅ Bot běží automaticky (1× denně)")

if st.button("🚀 Skenovat trh"):
    with st.spinner("Skenuji trh..."):
        df = scan_market()

    if df.empty:
        st.error("❌ Žádné vhodné akcie")
    else:
        st.subheader("🔥 Doporučené obchody")
        st.dataframe(df, use_container_width=True)

        for _, row in df.iterrows():
            send_telegram(
                f"🟢 BUY SIGNAL\n\n"
                f"Akcie: {row['Akcie']}\n"
                f"Cena: {row['Cena ($)']} USD\n"
                f"RSI: {row['RSI']}\n"
                f"AI skóre: {row['AI skóre']}"
            )
