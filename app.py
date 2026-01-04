import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
from textblob import TextBlob
import numpy as np

# =========================
# NASTAVENÍ
# =========================
KAPITAL_EUR = 500
USD_EUR = 0.92
RISK_PER_TRADE = 0.05

TRADING212_TICKERS = [
    "AAPL", "TSLA", "NVDA", "AMD", "META",
    "PLTR", "SOFI", "COIN", "NFLX", "INTC"
]

# =========================
st.set_page_config(
    page_title="Trading 212 Scanner",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Trading 212 – Rychlý výdělek")
st.write("Automatický výběr akcií + velikost pozice (kapitál 500 €)")

# =========================
def rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi_val = 100 - (100 / (1 + rs))
    return rsi_val

def sentiment(ticker):
    feed = feedparser.parse(
        f"https://news.google.com/rss/search?q={ticker}+stock"
    )
    score = 0
    count = 0
    for e in feed.entries[:5]:
        score += TextBlob(e.title).sentiment.polarity
        count += 1
    return round(score / count, 2) if count > 0 else 0

# =========================
if st.button("🚀 Skenovat trh"):
    output = []

    for t in TRADING212_TICKERS:
        data = yf.download(t, period="3mo", interval="1d", progress=False)

        if data is None or data.empty or len(data) < 30:
            continue

        data["RSI"] = rsi(data["Close"])
        data["EMA20"] = data["Close"].ewm(span=20).mean()

        last = data.iloc[-1]

        rsi_value = last["RSI"]
        if pd.isna(rsi_value):
            continue

        price = float(last["Close"])
        price_eur = price * USD_EUR

        volume_spike = (
            not pd.isna(last["Volume"]) and
            last["Volume"] > data["Volume"].mean() * 1.5
        )

        sent = sentiment(t)

        score = 0
        if rsi_value < 35:
            score += 2
        if volume_spike:
            score += 2
        if sent > 0:
            score += 1
        if last["Close"] > last["EMA20"]:
            score += 1

        signal = "HOLD"
        if score >= 4:
            signal = "🟢 KOUPIT"
        elif rsi_value > 70 and sent < 0:
            signal = "🔴 PRODAT"

        stop_loss_price = price * 0.97
        take_profit_price = price * 1.06

        risk_per_share = abs(price - stop_loss_price) * USD_EUR
        max_trade = KAPITAL_EUR * RISK_PER_TRADE

        shares = (
            int(max_trade / risk_per_share)
            if risk_per_share > 0 and signal == "🟢 KOUPIT"
            else "-"
        )

        output.append({
            "Akcie": t,
            "Cena ($)": round(price, 2),
            "Cena (€)": round(price_eur, 2),
            "RSI": round(rsi_value, 1),
            "Sentiment": sent,
            "Signál": signal,
            "Kolik koupit (ks)": shares,
            "Take Profit ($)": round(take_profit_price, 2),
            "Stop Loss ($)": round(stop_loss_price, 2)
        })

    df = pd.DataFrame(output)

    if not df.empty:
        df = df[df["Signál"] != "HOLD"].sort_values("RSI")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenalezeny žádné vhodné příležitosti.")

st.caption("⚠️ Není investiční doporučení. Používáš na vlastní riziko.")
