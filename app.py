import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime

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
# EVENT MAP (MOZEK)
# ======================
EVENT_MAP = {
    "venezuela": {
        "keywords": ["venezuela", "caracas"],
        "stocks": ["XOM", "CVX", "SHEL"],
        "weight": 100
    },
    "attack": {
        "keywords": ["attack", "strike", "explosion", "missile"],
        "stocks": ["LMT", "RTX", "XOM"],
        "weight": 80
    },
    "war": {
        "keywords": ["war", "invasion", "military"],
        "stocks": ["LMT", "RTX", "NOC", "XOM"],
        "weight": 120
    },
    "sanctions": {
        "keywords": ["sanctions", "embargo"],
        "stocks": ["XOM", "CVX", "SHEL"],
        "weight": 70
    }
}

# ======================
# NEWS FETCH
# ======================
def fetch_news():
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "language": "en",
        "category": "business",
        "apiKey": "demo"  # funguje omezeně, ale stabilně
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json().get("articles", [])
    except:
        return []

# ======================
# EVENT ANALYSIS
# ======================
def event_scan():
    news = fetch_news()
    hits = []

    for n in news:
        title = (n.get("title") or "").lower()

        for event, data in EVENT_MAP.items():
            if any(k in title for k in data["keywords"]):
                for stock in data["stocks"]:
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
    return result.head(5)

# ======================
# STREAMLIT UI
# ======================
st.set_page_config("🔥 LEVEL 3 – EVENT DRIVEN AI BOT", layout="centered")

st.title("🔥 LEVEL 3 – EVENT DRIVEN AI BOT")
st.warning("⚠️ Není investiční doporučení")

if st.button("🚨 ANALYZOVAT SVĚTOVÉ UDÁLOSTI"):
    df = event_scan()

    if df.empty:
        st.error("Žádné silné geopolitické události")
    else:
        st.subheader("📊 Nejpravděpodobnější akcie")
        st.dataframe(df, use_container_width=True)

        msg = (
            "🔥 *LEVEL 3 EVENT SIGNAL*\n"
            f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        )

        for _, r in df.iterrows():
            msg += (
                f"*{r['Akcie']}*\n"
                f"🧠 AI skóre: {r['Skóre']}\n"
                f"🎯 Confidence: {r['Confidence %']}%\n"
                f"📰 Zmínky: {r['Zmínky']}\n\n"
            )

        send_telegram(msg)
