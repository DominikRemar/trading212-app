import streamlit as st
import yfinance as yf
import pandas as pd
import feedparser
from textblob import TextBlob

# =========================
# NASTAVENÍ
# =========================
KAPITAL_EUR = 500
USD_EUR = 0.92   # orientační kurz
RISK_PER_TRADE = 0.05  # 5 % účtu

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
    return 100 - (100 / (1 + rs))

def sentiment(ticker):
    feed = feedparser.parse(
        f"https://news.google.com/rss/search?q={ticker}+stock"
    )
    score = 0
    for e in feed.entries[:5]:
        score += TextBlob(e.title).sentiment.polarity
    return round(score, 2)

# =========================
if st.button("🚀 Skenovat trh"):
    output = []

    for t in TRADING212_TICKERS:
        data = yf.download(t, period="3mo", interval="1d", progress=False)
        if len(data) < 30:
            continue

        data["RSI"] = rsi(data["Close"])
        data["EMA20"] = data["Close"].ewm(span=20).mean()

        last = data.iloc[-1]
        price = float(last["Close"])
        price_eur = price * USD_EUR

        volume_spike = last["Volume"] > data["Volume"].mean() * 1.5
        sent = sentiment(t)

        score = 0
        if last["RSI"] < 35:
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
        elif last["RSI"] > 70 and sent < 0:
            signal = "🔴 PRODAT"

        max_trade = KAPITAL_EUR * RISK_PER_TRADE
        stop_loss_price = price * 0.97
        take_profit_price = price * 1.06

        risk_per_share = abs(price - stop_loss_price) * USD_EUR
        shares = int(max_trade / risk_per_share) if risk_per_share > 0 else 0

        output.append({
            "Akcie": t,
            "Cena ($)": round(price, 2),
            "Cena (€)": round(price_eur, 2),
            "RSI": round(last["RSI"], 1),
            "Sentiment": sent,
            "Signál": signal,
            "Kolik koupit (ks)": shares if signal == "🟢 KOUPIT" else "-",
            "Take Profit ($)": round(take_profit_price, 2),
            "Stop Loss ($)": round(stop_loss_price, 2)
        })

    df = pd.DataFrame(output)
    df = df[df["Signál"] != "HOLD"].sort_values("RSI")
    st.dataframe(df, use_container_width=True)

st.caption("⚠️ Není investiční doporučení. Používáš na vlastní riziko.")
