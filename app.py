import streamlit as st
import requests
import time
from datetime import datetime

# =======================
# CONFIG
# =======================
TELEGRAM_TOKEN = "8245860410:AAFK59QMTb7r5cY4VcJzqFt46tTh4y45ufM"
TELEGRAM_CHAT_ID = "7772237988"

NEWS_KEYWORDS = [
    "venezuela", "usa", "attack", "strike", "sanctions",
    "war", "oil", "pipeline", "military", "conflict",
    "iran", "middle east", "energy crisis"
]

STOCK_MAP = {
    "oil": ["XOM", "CVX", "SHEL"],
    "energy": ["XOM", "CVX", "SHEL"],
    "war": ["LMT", "RTX", "NOC"],
    "military": ["LMT", "RTX", "NOC"]
}

AGGRESSIVE_MODE = True
CHECK_INTERVAL = 300  # 5 minut

# =======================
# FUNCTIONS
# =======================
def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def fetch_news():
    # jednoduchý veřejný zdroj (bez API klíče)
    url = "https://r.jina.ai/https://news.google.com/rss/search?q=venezuela+usa+oil+attack+war"
    try:
        r = requests.get(url, timeout=10)
        return r.text.lower()
    except:
        return ""

def analyze_news(text):
    score = 0
    found = []
    for kw in NEWS_KEYWORDS:
        if kw in text:
            score += 1
            found.append(kw)
    return score, found

def generate_signal(score, keywords):
    if score < (2 if AGGRESSIVE_MODE else 4):
        return None

    stocks = set()
    for kw in keywords:
        for key in STOCK_MAP:
            if key in kw:
                stocks.update(STOCK_MAP[key])

    if not stocks:
        stocks = {"XOM", "CVX", "SHEL"}

    confidence = min(100, score * 15)

    msg = f"""🔥 *LEVEL 5 – AUTO EVENT SIGNAL*
🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}

📊 *AI skóre:* {score * 100}
🎯 *Confidence:* {confidence}%
📰 *Zprávy:* {", ".join(keywords)}

📈 *Akcie:* {", ".join(stocks)}

⚠️ Není investiční doporučení
"""
    return msg

# =======================
# STREAMLIT UI
# =======================
st.set_page_config(page_title="LEVEL 5 AUTO EVENT AI BOT", layout="centered")
st.title("🔥 LEVEL 5 – AUTO EVENT AI BOT")
st.warning("Není investiční doporučení")

auto = st.checkbox("🤖 AUTO MODE (běží sám)", value=True)

status_box = st.empty()

if auto:
    status_box.info("🟢 Bot běží nonstop a sleduje světové události")

    if "last_run" not in st.session_state:
        st.session_state.last_run = 0

    now = time.time()
    if now - st.session_state.last_run > CHECK_INTERVAL:
        news = fetch_news()
        score, keywords = analyze_news(news)
        signal = generate_signal(score, keywords)

        if signal:
            send_telegram(signal)
            status_box.success("🔥 Silný event detekován – odesláno na Telegram")
        else:
            status_box.info("📭 Momentálně žádné výrazné geopolitické eventy")

        st.session_state.last_run = now

else:
    if st.button("🚨 MANUÁLNÍ ANALÝZA"):
        news = fetch_news()
        score, keywords = analyze_news(news)
        signal = generate_signal(score, keywords)

        if signal:
            st.success("🔥 EVENT NALEZEN")
            st.code(signal)
        else:
            st.info("📭 Žádný silný event")
