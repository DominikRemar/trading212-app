import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# ======================
# NASTAVENÍ
# ======================
KAPITAL_CZK = 5000
USD_CZK = 23
RISK = 0.5

TICKERS = ["AAPL", "TSLA", "NVDA", "AMD", "META", "PLTR", "COIN", "SOFI"]

st.set_page_config(page_title="Trading 212 – AI Polo-automat", page_icon="🤖")
st.title("📈 Trading 212 – AI Polo-automat")
st.caption("⚠️ Není investiční doporučení")

# ======================
def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def ai_score(rsi, trend):
    score = 0
    if rsi < 30:
        score += 60
    elif rsi < 40:
        score += 40
    if trend:
        score += 20
    return score

# ======================
st.selectbox("🧠 Režim", ["SAFE"])
st.success("✅ Připraveno – klikni na Skenovat trh")

# ======================
if st.button("🚀 Skenovat trh"):
    with st.spinner("🔎 Skenuji trh..."):
        results = []

        for ticker in TICKERS:
            try:
                df = yf.download(ticker, period="3mo", progress=False)
                if df.empty or len(df) < 30:
                    continue

                df["RSI"] = calculate_rsi(df["Close"])
                df["EMA20"] = df["Close"].ewm(span=20).mean()

                rsi_value = float(df["RSI"].iloc[-1])
                price = float(df["Close"].iloc[-1])
                ema = float(df["EMA20"].iloc[-1])

                if np.isnan(rsi_value):
                    continue

                price_czk = price * USD_CZK
                trend_up = price > ema
                score = ai_score(rsi_value, trend_up)

                signal = "HOLD"
                if score >= 60:
                    signal = "🟢 KOUPIT"
                elif rsi_value > 70:
                    signal = "🔴 PRODAT"

                invest = KAPITAL_CZK * RISK
                kusy = int(invest / price_czk) if signal == "🟢 KOUPIT" else "-"

                results.append({
                    "Akcie": ticker,
                    "Cena ($)": round(price, 2),
                    "Cena (Kč)": round(price_czk, 0),
                    "RSI": round(rsi_value, 1),
                    "AI skóre": score,
                    "Signál": signal,
                    "Kusy": kusy
                })

            except Exception:
                continue

        df_res = pd.DataFrame(results)
        df_res = df_res[df_res["Signál"] != "HOLD"].sort_values("AI skóre", ascending=False)

        if df_res.empty:
            st.warning("❌ Nenalezeny žádné vhodné akcie")
        else:
            st.subheader("🔥 Doporučené obchody")
            st.dataframe(df_res, use_container_width=True)
