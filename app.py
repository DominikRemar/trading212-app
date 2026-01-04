import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests

# =========================
# NASTAVENÍ
# =========================
KAPITAL_CZK = 5000
USD_CZK = 23
RISK_PER_TRADE = 0.5  # 50 % kapitálu max na obchod

TICKERS = ["AAPL", "TSLA", "NVDA", "AMD", "META", "PLTR", "COIN", "SOFI"]

# =========================
st.set_page_config(page_title="Trading 212 – AI Polo-automat", page_icon="🤖")

st.title("📈 Trading 212 – AI Polo-automat")
st.caption("⚠️ Není investiční doporučení")

# =========================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def ai_score(rsi_value, trend):
    score = 0
    if rsi_value < 30:
        score += 50
    elif rsi_value < 40:
        score += 30

    if trend:
        score += 20

    return score

# =========================
mode = st.selectbox("🧠 Režim", ["SAFE", "NORMAL"])

st.success("✅ Připraveno – klikni na Skenovat trh")

# =========================
if st.button("🚀 Skenovat trh"):
    with st.spinner("🔎 Skenuji trh..."):
        results = []

        for t in TICKERS:
            data = yf.download(t, period="3mo", progress=False)
            if len(data) < 30:
                continue

            data["RSI"] = rsi(data["Close"])
            data["EMA20"] = data["Close"].ewm(span=20).mean()

            last = data.iloc[-1]

            if pd.isna(last["RSI"]):
                continue

            price_usd = float(last["Close"])
            price_czk = price_usd * USD_CZK

            trend_up = price_usd > last["EMA20"]
            score = ai_score(last["RSI"], trend_up)

            signal = "HOLD"
            if score >= 60:
                signal = "🟢 KOUPIT"
            elif last["RSI"] > 70:
                signal = "🔴 PRODAT"

            invest = KAPITAL_CZK * RISK_PER_TRADE
            kusy = int(invest / price_czk)

            results.append({
                "Akcie": t,
                "Cena ($)": round(price_usd, 2),
                "Cena (Kč)": round(price_czk, 0),
                "RSI": round(last["RSI"], 1),
                "AI skóre": score,
                "Signál": signal,
                "Kusy": kusy if signal == "🟢 KOUPIT" else "-"
            })

        df = pd.DataFrame(results)
        df = df[df["Signál"] != "HOLD"].sort_values("AI skóre", ascending=False)

        if df.empty:
            st.warning("❌ Nic vhodného nenalezeno")
        else:
            st.subheader("🔥 Doporučené akcie")
            st.dataframe(df, use_container_width=True)
