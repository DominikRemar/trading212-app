import streamlit as st
import requests
from datetime import datetime

# ======================
# TELEGRAM
# ======================
TELEGRAM_TOKEN = "8245860410:AAFK59QMTb7r5cY4VcJzqFt46tTh4y45ufM"
TELEGRAM_CHAT_ID = "7772237988"

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": msg,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            },
            timeout=10
        )
    except:
        pass

# ======================
# SOCIAL + EVENT ENGINE
# ======================
KEYWORDS = {
    "venezuela": 4, "usa": 2, "attack": 4, "strike": 4,
    "war": 4, "sanctions": 3, "oil": 4, "gas": 3,
    "pipeline": 4, "shipping": 3, "energy": 2,
    "surge": 2, "rally": 2, "breakout": 2,
    "military": 3, "conflict": 3
}

STOCK_BUCKETS = {
    "oil": ["XOM", "CVX", "OXY", "PBR", "DVN"],
    "gas": ["EQT", "CHK", "SWN"],
    "shipping": ["ZIM", "GNK", "DAC"],
    "energy": ["XLE", "HAL", "SLB"],
    "war": ["LMT", "RTX", "NOC"],
    "military": ["LMT", "RTX", "NOC"]
}

NEWS_URLS = [
    "https://r.jina.ai/https://news.google.com/rss/search?q=venezuela+oil+attack",
    "https://r.jina.ai/https://news.google.com/rss/search?q=war+energy+shipping",
    "https://r.jina.ai/https://www.reddit.com/r/worldnews/.rss",
    "https://r.jina.ai/https://www.reddit.com/r/stocks/.rss"
]

def fetch_social_news():
    text = ""
    for url in NEWS_URLS:
        try:
            text += requests.get(url, timeout=10).text.lower()
        except:
            continue
    return text

def analyze_text(text):
    score = 0
    hits = []
    for k, w in KEYWORDS.items():
        if k in text:
            score += w
            hits.append(k)
    return score, list(set(hits))

def pick_stocks(hits):
    picks = set()
    for h in hits:
        for key in STOCK_BUCKETS:
            if key in h:
                picks.update(STOCK_BUCKETS[key])
    if not picks:
        picks = {"XLE", "OXY", "HAL"}  # fallback – vždy něco
    return list(picks)

# ======================
# STREAMLIT UI
# ======================
st.set_page_config("LEVEL 5.5 – SOCIAL EVENT AI", layout="centered")
st.title("🔥 LEVEL 5.5 – SOCIAL + EVENT AI BOT")
st.warning("Není investiční doporučení")

st.markdown("👉 Klikni a bot **projede zprávy + sociální sentiment (X/Reddit-like)**")

if st.button("🚀 SPUSTIT ANALÝZU"):
    with st.spinner("Analyzuji sociální a geopolitická data..."):
        text = fetch_social_news()
        score, hits = analyze_text(text)
        stocks = pick_stocks(hits)

    confidence = min(100, score * 5)

    if score >= 8:
        header = "🔥 *SILNÝ EVENT SIGNAL*"
    else:
        header = "⚠️ *SLABŠÍ / HYPE EVENT*"

    msg = f"""{header}
🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}

🧠 AI skóre: {score}
🎯 Confidence: {confidence}%

📰 Klíčová slova:
{", ".join(hits) if hits else "obecný sentiment"}

📈 Kandidáti:
{", ".join(stocks)}

⚠️ Není investiční doporučení
"""

    send_telegram(msg)
    st.success("📨 Odesláno na Telegram")
    st.code(msg)
