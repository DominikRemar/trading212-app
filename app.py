# ======================
# IMPORTY
# ======================
import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import time
import hashlib
from datetime import datetime

# ======================
# API KLÍČE
# ======================
NEWS_API_KEY = "bf83b379d110436dbbf648aaff1e5d8e"

TELEGRAM_TOKEN = "8245860410:AAFK59QMTb7r5cY4VcJzqFt46tTh4y45ufM"
TELEGRAM_CHAT_ID = "7772237988"

# ======================
# TELEGRAM
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
    except:
        pass

# ======================
# LEVEL 3 EVENT MAPA
# ======================
EVENT_MAP = {
    "venezuela_oil": {
        "keywords": ["venezuela", "caracas"],
        "stocks": ["XOM","CVX","SHEL"],
        "weight": 50
    },
    "war_attack": {
        "keywords": ["war","attack","strike","missile","explosion"],
        "stocks": ["LMT","RTX","NOC","XOM"],
        "weight": 45
    },
    "sanctions": {
        "keywords": ["sanctions","embargo"],
        "stocks": ["XOM","CVX","SHEL"],
        "weight": 35
    }
}

ALL_STOCKS = sorted(set(sum([v["stocks"] for v in EVENT_MAP.values()], [])))

# ======================
# NEWS FETCH
# ======================
def fetch_news():
    url = (
        "https://newsapi.org/v2/top-headlines?"
        f"language=en&pageSize=30&apiKey={NEWS_API_KEY}"
    )
    r = requests.get(url, timeout=10)
    return r.json().get("articles", [])

# ======================
# EVENT ANALÝZA + CONFIRMATION
# ======================
def analyze_events():
    news = fetch_news()
    rows = []

    for n in news:
        title = n.get("title","")
        if not title:
            continue

        text = title.lower()

        for event, data in EVENT_MAP.items():
            if any(k in text for k in data["keywords"]):
                for stock in data["stocks"]:
                    rows.append({
                        "Akcie": stock,
                        "Event": event,
                        "Event skóre": data["weight"],
                        "Zpráva": title
                    })

    return pd.DataFrame(rows)

# ======================
# TRŽNÍ POTVRZENÍ (ROPA + VIX)
# ======================
def market_confirmation():
    score = 0

    try:
        oil = yf.Ticker("CL=F").history(period="5d")["Close"]
        if oil.iloc[-1] > oil.iloc[-2]:
            score += 10
    except:
        pass

    try:
        vix = yf.Ticker("^VIX").history(period="5d")["Close"]
        if vix.iloc[-1] > vix.iloc[-2]:
            score += 5
    except:
        pass

    return score

# ======================
# TECHNICKÁ KONFIRMACE
# ======================
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def technical_score(symbol):
    try:
        data = yf.Ticker(symbol).history(period="6mo")
        if len(data) < 60:
            return 0

        close = data["Close"]
        price = close.iloc[-1]
        rsi = compute_rsi(close).iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1]
        change_30d = ((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100

        score = 0
        if price > ma200: score += 15
        if 35 <= rsi <= 65: score += 10
        if change_30d > 0: score += 10
        return score
    except:
        return 0

# ======================
# LEVEL 3 FINÁLNÍ SCAN
# ======================
def level3_scan():
    event_df = analyze_events()
    if event_df.empty:
        return pd.DataFrame()

    summary = (
        event_df.groupby("Akcie")
        .agg({
            "Event skóre":"sum",
            "Zpráva":"count"
        })
        .rename(columns={"Zpráva":"Zmínky"})
        .reset_index()
    )

    summary["Tech skóre"] = summary["Akcie"].apply(technical_score)
    summary["Market skóre"] = market_confirmation()
    summary["AI skóre"] = (
        summary["Event skóre"] +
        summary["Tech skóre"] +
        summary["Market skóre"] +
        summary["Zmínky"] * 5
    )

    summary["Confidence %"] = (summary["AI skóre"] / summary["AI skóre"].max() * 100).round(0)

    return summary.sort_values("AI skóre", ascending=False).head(3)

# ======================
# STREAMLIT UI + AUTO MODE
# ======================
st.set_page_config("LEVEL 3 EVENT AI", layout="centered")
st.title("🔥🤖 LEVEL 3 – EVENT DRIVEN AI BOT")
st.warning("⚠️ Není investiční doporučení")

AUTO_INTERVAL = 600  # 10 minut

if "last_run" not in st.session_state:
    st.session_state.last_run = 0
if "last_alert" not in st.session_state:
    st.session_state.last_alert = ""

now = time.time()

if now - st.session_state.last_run >= AUTO_INTERVAL:
    st.session_state.last_run = now

    df = level3_scan()

    if not df.empty and df.iloc[0]["AI skóre"] >= 70:
        alert_hash = hashlib.md5(df.to_string().encode()).hexdigest()

        if alert_hash != st.session_state.last_alert:
            st.session_state.last_alert = alert_hash

            msg = (
                f"🔥 *LEVEL 3 EVENT SIGNAL*\n"
                f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
            )

            for _, r in df.iterrows():
                msg += (
                    f"*{r['Akcie']}*\n"
                    f"🧠 AI skóre: {r['AI skóre']}\n"
                    f"🎯 Confidence: {r['Confidence %']}%\n"
                    f"📰 Zmínky: {r['Zmínky']}\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"
                )

            send_telegram(msg)

    st.experimental_rerun()

st.info("🤖 AUTO MODE aktivní – sken každých 10 minut")
