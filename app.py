import streamlit as st
import requests
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
    url = "https://r.jina.ai/https://news.google.com/rss/search?q=venezuela+usa+oil+attack+war+sanctions"
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
    return score, list(set(found))

def generate_signal(score, keywords):
    if score < 2:
        return None

    stocks = set()
    for kw in keywords:
        for key in STOCK_MAP:
            if key in kw:
                stocks.update(STOCK_MAP[key])

    if not stocks:
        stocks = {"XOM", "CVX", "SHEL"}

    confidence = min(100, score * 20)

    msg = f"""🔥 *LEVEL 5 – MANUAL EVENT SIGNAL*
🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}

📊 *AI skóre:* {score * 100}
🎯 *Confidence:* {confidence}%
📰 *Klíčová slova:* {", ".join(keywords)}

📈 *Akcie:* {", ".join(stocks)}

⚠️ Není investiční doporučení
"""
    return msg

# =======================
# STREAMLIT UI
# =======================
st.set_page_config(page_title="LEVEL 5 – MANUAL EVENT AI BOT", layout="centered")
st.title("🔥 LEVEL 5 – MANUAL EVENT AI BOT")
st.warning("Není investiční doporučení")

st.markdown("👉 Klikni na tlačítko a bot **okamžitě projede světové zprávy**")

if st.button("🚨 SPUSTIT KOMPLETNÍ ANALÝZU"):
    with st.spinner("Analyzuji geopolitické zprávy..."):
        news = fetch_news()
        score, keywords = analyze_news(news)
        signal = generate_signal(score, keywords)

    if signal:
        send_telegram(signal)
        st.success("🔥 SILNÝ EVENT NALEZEN – ODESLÁNO NA TELEGRAM")
        st.code(signal)
    else:
        st.info("📭 Momentálně žádné dostatečně silné geopolitické eventy")
