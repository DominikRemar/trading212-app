# ======================
# IMPORTY
# ======================
import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime
from transformers import pipeline

# ======================
# API KLÍČE (UŽ VLOŽENO)
# ======================
NEWS_API_KEY = "bf83b379d110436dbbf648aaff1e5d8e"

TELEGRAM_TOKEN = "8245860410:AAFK59QMTb7r5cY4VcJzqFt46tTh4y45ufM"
TELEGRAM_CHAT_ID = "7772237988"

# ======================
# TELEGRAM FUNKCE
# ======================
def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            },
            timeout=10
        )
    except Exception as e:
        print(e)

# ======================
# AI SENTIMENT MODEL
# ======================
sentiment_ai = pipeline("sentiment-analysis")

# ======================
# MAPA TÉMAT → AKCIE
# ======================
THEME_MAP = {
    "oil": ["XOM","CVX","SHEL"],
    "energy": ["XOM","CVX","NEE"],
    "war": ["LMT","RTX","NOC"],
    "attack": ["LMT","RTX","NOC"],
    "defense": ["LMT","RTX","NOC"],
    "ai": ["NVDA","AMD","MSFT"],
    "chips": ["NVDA","AMD","TSM"],
    "banks": ["JPM","GS","BAC"],
    "crypto": ["COIN","MSTR"],
}

ALL_STOCKS = sorted(set(sum(THEME_MAP.values(), [])))

# ======================
# NEWS FETCH + ANALÝZA
# ======================
def fetch_news():
    url = (
        "https://newsapi.org/v2/top-headlines?"
        f"language=en&pageSize=15&apiKey={NEWS_API_KEY}"
    )
    r = requests.get(url, timeout=10)
    return r.json().get("articles", [])

def analyze_news():
    news = fetch_news()
    signals = []

    for n in news:
        title = n.get("title", "")
        if not title:
            continue

        sentiment = sentiment_ai(title)[0]
        score = 0
        topics = []

        text = title.lower()
        for topic in THEME_MAP:
            if topic in text:
                topics.append(topic)
                score += 25

        if sentiment["label"] == "POSITIVE":
            score += 10
        elif sentiment["label"] == "NEGATIVE":
            score += 5  # krize = bullish pro sektor

        for topic in topics:
            for stock in THEME_MAP[topic]:
                signals.append({
                    "Akcie": stock,
                    "News skóre": score,
                    "Téma": topic,
                    "Zpráva": title
                })

    return pd.DataFrame(signals)

# ======================
# TECHNICKÉ INDIKÁTORY
# ======================
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ======================
# MARKET SCAN
# ======================
def scan_market(news_df):
    results = []

    for symbol in ALL_STOCKS:
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="6mo")
            if len(data) < 60:
                continue

            close = data["Close"]
            price = float(close.iloc[-1])
            rsi = compute_rsi(close).iloc[-1]
            ma200 = close.rolling(200).mean().iloc[-1]
            change_30d = ((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100

            tech_score = 0
            if price > ma200: tech_score += 25
            if 30 <= rsi <= 70: tech_score += 20
            if change_30d > 0: tech_score += 15

            news_score = 0
            if not news_df.empty:
                news_score = news_df[news_df["Akcie"] == symbol]["News skóre"].sum()

            total_score = tech_score + news_score

            results.append({
                "Akcie": symbol,
                "Cena": round(price,2),
                "RSI": round(rsi,1),
                "30d %": round(change_30d,1),
                "Tech skóre": tech_score,
                "News skóre": news_score,
                "AI skóre": total_score,
                "TP": round(price * 1.12,2),
                "SL": round(price * 0.94,2)
            })

        except:
            continue

    return pd.DataFrame(results).sort_values("AI skóre", ascending=False).head(5)

# ======================
# STREAMLIT UI
# ======================
st.set_page_config("AI NEWS TRADING BOT", layout="centered")
st.title("🌍📈 AI NEWS TRADING BOT")
st.warning("⚠️ Není investiční doporučení")

if st.button("🚨 Skenovat svět & trhy"):
    news_df = analyze_news()
    market_df = scan_market(news_df)

    if market_df.empty:
        st.error("❌ Žádné signály")
        send_telegram("❌ Dnes žádné AI news signály")
        st.stop()

    st.subheader("🔥 Akcie reagující na světové události")
    st.dataframe(market_df, use_container_width=True)

    msg = (
        f"🚨 *AI NEWS SIGNÁLY*\n"
        f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    for _, row in market_df.iterrows():
        msg += (
            f"*{row['Akcie']}*\n"
            f"💰 Cena: ${row['Cena']}\n"
            f"🎯 TP: ${row['TP']}\n"
            f"🛑 SL: ${row['SL']}\n"
            f"🧠 Tech: {row['Tech skóre']} | News: {row['News skóre']}\n"
            f"🔥 AI skóre: {row['AI skóre']}\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
        )

    send_telegram(msg)
