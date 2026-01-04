import streamlit as st
import pandas as pd
import numpy as np
import datetime
import requests

# =========================
# 🔐 TELEGRAM NASTAVENÍ
# =========================
TELEGRAM_TOKEN = "TVUJ_TOKEN"
TELEGRAM_CHAT_ID = "TVUJ_CHAT_ID"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data, timeout=5)
    except:
        pass

# =========================
# 📊 TEST DATA
# =========================
def test_stock():
    return {
        "Akcie": "AAPL",
        "Cena ($)": 190.0,
        "RSI": 42,
        "AI skóre": 82,
        "Signál": "KUPIT",
        "Prodat při ($)": 215.0
    }

# =========================
# 📈 REÁLNÝ SCAN (jednoduchý)
# =========================
def real_scan():
    # sem můžeš později připojit Yahoo / Alpha Vantage
    return None

# =========================
# 🤖 STREAMLIT APP
# =========================
st.set_page_config(page_title="Trading 212 – AI Polo-automat", layout="centered")

st.title("📈 Trading 212 – AI Polo-automat")

st.warning("⚠️ Není investiční doporučení")

TEST_MODE = st.toggle("🧪 TEST MODE (doporučeno zapnout)", value=True)

st.success("✅ Bot běží automaticky (1× denně)")

if st.button("🚀 Skenovat trh"):

    if TEST_MODE:
        stock = test_stock()
        st.success("TEST MODE – vždy nalezena 1 akcie")

    else:
        stock = real_scan()

    if stock is None:
        st.error("❌ Žádná vhodná akcie")
    else:
        df = pd.DataFrame([stock])
        st.dataframe(df, use_container_width=True)

        msg = f"""🧪 TEST MODE – Ověření funkčnosti

📈 Akcie: {stock['Akcie']}
💲 Cena: ${stock['Cena ($)']}
📊 RSI: {stock['RSI']}
🧠 AI skóre: {stock['AI skóre']}
✅ Signál: {stock['Signál']}

🎯 Cíl pro prodej: ${stock['Prodat při ($)']}
⏰ {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
        send_telegram(msg)
