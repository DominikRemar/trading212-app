import streamlit as st
import pandas as pd

# =========================
# NASTAVENÍ
# =========================
KAPITAL_EUR = 500
USD_EUR = 0.92
RISK_PER_TRADE = 0.05

TICKERS = [
    "AAPL", "TSLA", "NVDA", "AMD", "META",
    "PLTR", "SOFI", "COIN", "NFLX", "INTC"
]

# =========================
st.set_page_config(
    page_title="Trading 212 – Rychlý výdělek",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Trading 212 – Rychlý výdělek")
st.success("✅ Aplikace připravena. Klikni na **Skenovat trh**")

st.caption("⚠️ Není investiční doporučení. Používáš na vlastní riziko.")

# =========================
def rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# =========================
if st.button("🚀 Skenovat trh"):
    import yfinance as yf
    import feedparser
    from textblob import TextBlob

    st.info("🔎 Skenuji trh... vydrž pár sekund")

    results = []

    for t in TICKERS:
        try:
            data = yf.download(
                t,
                period="1mo",
                interval="1d",
                progress=False,
                auto_adjust=True
            )

            if data.empty or len(data) < 20:
                continue

            data["RSI"] = rsi(data["Close"])
            data["EMA20"] = data["Close"].ewm(span=20).mean()

            last = data.iloc[-1]
            price = float(last["Close"])
            price_eur = price * USD_EUR

            volume_spike = last["Volume"] > data["Volume"].mean() * 1.5

            # Sentiment (zjednodušený a rychlý)
            feed = feedparser.parse(
                f"https://news.google.com/rss/search?q={t}+stock"
            )
            sent = sum(
                TextBlob(e.title).sentiment.polarity
                for e in feed.entries[:3]
            )

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

            stop_loss = price * 0.97
            take_profit = price * 1.06

            risk_per_share = abs(price - stop_loss) * USD_EUR
            max_risk = KAPITAL_EUR * RISK_PER_TRADE
            shares = int(max_risk / risk_per_share) if risk_per_share > 0 else 0

            results.append({
                "Akcie": t,
                "Cena (€)": round(price_eur, 2),
                "RSI": round(last["RSI"], 1),
                "Objem spike": "ANO" if volume_spike else "NE",
                "Sentiment": round(sent, 2),
                "Signál": signal,
                "Kolik koupit (ks)": shares if signal == "🟢 KOUPIT" else "-",
                "Take Profit ($)": round(take_profit, 2),
                "Stop Loss ($)": round(stop_loss, 2)
            })

        except Exception:
            continue

    df = pd.DataFrame(results)

    if df.empty:
        st.warning("❌ Nic vhodného nenalezeno")
    else:
        # SELL ALERTY
        sell_df = df[df["Signál"] == "🔴 PRODAT"]
        if not sell_df.empty:
            st.error("🚨 SELL ALERT")
            st.dataframe(sell_df, use_container_width=True)

        # TOP 3 BUY
        buy_df = df[df["Signál"] == "🟢 KOUPIT"].head(3)

        if buy_df.empty:
            st.warning("⚠️ Žádná silná BUY příležitost")
        else:
            st.success("🔥 TOP 3 AKCIE NA RYCHLÝ ZISK")
            st.dataframe(buy_df, use_container_width=True)
