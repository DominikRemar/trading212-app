import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime, timedelta
import time

# ======================
# TELEGRAM
# ======================
TELEGRAM_TOKEN = "8245860410:AAFK59QMTb7r5cY4VcJzqFt46tTh4y45ufM"
TELEGRAM_CHAT_ID = "7772237988"

def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown"
            },
            timeout=10
        )
    except:
        pass

# ======================
# EVENT MAP – LEVEL 4
# ======================
EVENT_MAP = {
    "venezuela": {
        "keywords": ["venezuela", "caracas"],
        "stocks": ["XOM", "CVX", "SHEL"],
        "weight": 120
    },
    "war": {
        "keywords": ["war", "invasion", "military"],
        "stocks": ["LMT", "RTX", "NOC", "XOM"],
        "weight": 150
    },
    "attack": {
        "keywords": ["attack", "strike", "explosion", "missile"],
        "stocks": ["LMT", "RTX", "XOM"],
        "weight": 100
    },
    "sanctions": {
        "keywords": ["sanctions", "embargo"],
        "stocks": ["XOM", "CVX", "SHEL"],
        "weight": 90
    }
}

# ======================
# NEWS FETCH (STABLE)
# ======================
def fetch_news():
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "language": "en",
        "category": "business",
        "apiKey": "demo"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json().get("articles", [])
    except:
        return []

# ======================
# TREND CONFIRMATION
# ======================
def trend_ok(symbol):
    try:
        data = yf.Ticker(symbol).history(period="3mo")
        if len(data) < 30:
            return False
        ma20 = data["Close"].rolling(20).mean().iloc[-1]
        price = data["Close"].iloc[-1]
        return price > ma20
    except:
        return False

# ======================
# LEVEL 4 EVENT SCAN
# ======================
def level4_scan():
    news = fetch_news()
    hits = []

    for n in news:
        title = (n.get("title") or "").lower()

        for event, data in EVENT_MAP.items():
            if any(k in title for k in data["keywords"]):
                for stock in data["stocks"]:
                    if trend_ok(stock):
                        hits.append({
                            "Akcie": stock,
                            "Skóre": data["weight"],
                            "Zpráva": n.get("title")
                        })

    if not hits:
        return pd.DataFrame()

    df = pd.DataFrame(hits)

    result = (
        df.groupby("Akcie")
        .agg({
            "Skóre": "sum",
            "Zpráva": "count"
        })
        .rename(columns={"Zpráva": "Zmínky"})
        .sort_values("Skóre", ascending=False)
        .reset_index()
    )

    result["Confidence %"] = (result["Skóre"] / result["Skóre"].max() * 100).round(1)
    return result[result["Skóre"] >= 150].head(3)

# ======================
# STREAMLIT UI
# ======================
st.set_page_config("🔥 LEVEL 4 – AUTO EVENT AI BOT", layout="centered")

st.title("🔥 LEVEL 4 – AUTO EVENT AI BOT")
st.warning("⚠️ Není investiční doporučení")

AUTO = st.checkbox("🤖 AUTO MODE (běží sám)", value=False)

if st.button("🚨 MANUÁLNÍ ANALÝZA") or AUTO:
    df = level4_scan()

    if df.empty:
        st.info("Žádný dostatečně silný event")
    else:
        st.subheader("📊 TOP EVENT AKCIE")
        st.dataframe(df, use_container_width=True)

        msg = (
            "🔥 *LEVEL 4 EVENT SIGNAL*\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        )

        for _, r in df.iterrows():
            price = yf.Ticker(r["Akcie"]).history(period="1d")["Close"].iloc[-1]
            tp = round(price * 1.1, 2)
            sl = round(price * 0.95, 2)

            msg += (
                f"*{r['Akcie']}*\n"
                f"💰 Cena: {round(price,2)}\n"
                f"🎯 TP: {tp}\n"
                f"🛑 SL: {sl}\n"
                f"🧠 Skóre: {r['Skóre']}\n"
                f"🎯 Confidence: {r['Confidence %']}%\n"
                f"📰 Zmínky: {r['Zmínky']}\n\n"
            )

        send_telegram(msg)

    if AUTO:
        time.sleep(900)  # 15 minut
