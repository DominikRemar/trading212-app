import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests

# =====================
# NASTAVENÍ
# =====================
INVEST_KC = 5000
USD_CZK = 23
WATCHLIST = ["AAPL", "MSFT", "NVDA", "META", "GOOGL", "TSLA", "AMZN", "COIN"]

# =====================
# TELEGRAM
# =====================
def send_telegram(msg):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg})
    except:
        pass

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
# STREAMLIT UI
# =====================
st.set_page_config(page_title="Trading 212 – AI Polo-automat", layout="centered")

st.title("📈 Trading 212 – AI Polo-automat")
st.warning("⚠️ Není investiční doporučení")

mode = st.selectbox("🧠 Režim", ["SAFE"])
st.success("✅ Připraveno – klikni na Skenovat trh")

# =====================
# BUTTON
# =====================
if st.button("🚀 Skenovat trh"):
    results = []

    for ticker in WATCHLIST:
        try:
            df = yf.download(ticker, period="3mo", interval="1d", progress=False)
            if df.empty:
                continue

            df["RSI"] = rsi(df["Close"])
            last = df.iloc[-1]

            if pd.isna(last["RSI"]):
                continue

            price_usd = float(last["Close"])
            price_kc = price_usd * USD_CZK
            pieces = int(INVEST_KC // price_kc)

            # AI skóre (jednoduché, ale funkční)
            ai_score = 0
            if last["RSI"] < 35:
                ai_score += 40
            if df["Close"].iloc[-1] > df["Close"].rolling(20).mean().iloc[-1]:
                ai_score += 30
            if df["Close"].pct_change().iloc[-5:].mean() > 0:
                ai_score += 30

            signal = "ČEKAT"
            if last["RSI"] < 30 and ai_score >= 60:
                signal = "KUPIT"
            elif last["RSI"] > 70:
                signal = "PRODAT"

            results.append({
                "Akcie": ticker,
                "Cena ($)": round(price_usd, 2),
                "Cena (Kč)": int(price_kc),
                "RSI": round(last["RSI"], 1),
                "AI skóre": ai_score,
                "Signál": signal,
                "Kusy": pieces
            })

        except:
            continue

    if not results:
        st.error("❌ Žádné vhodné akcie")
    else:
        df_res = pd.DataFrame(results)

        # jen 1 nejsilnější akcie
        df_res = df_res.sort_values("AI skóre", ascending=False).head(1)

        st.subheader("🔥 Doporučený obchod")
        st.dataframe(df_res, use_container_width=True)

        row = df_res.iloc[0]

        if row["Signál"] != "ČEKAT":
            send_telegram(
                f"📈 Trading 212 AI ALERT\n\n"
                f"Akcie: {row['Akcie']}\n"
                f"Signál: {row['Signál']}\n"
                f"Cena: {row['Cena (Kč)']} Kč\n"
                f"RSI: {row['RSI']}\n"
                f"AI skóre: {row['AI skóre']}\n"
                f"Kusy za {INVEST_KC} Kč: {row['Kusy']}"
            )
