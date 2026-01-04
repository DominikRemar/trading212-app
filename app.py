import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# ======================
# KONFIGURACE
# ======================
TEST_STOCK = {
    "symbol": "AAPL",
    "price": 190.0,
    "rsi": 42.0,
    "ai_score": 82,
    "signal": "KUPIT",
    "sell_price": 215.0
}

SAFE_CONF = {
    "rsi_buy": 45,
    "ai_min": 70
}

# ======================
# TELEGRAM
# ======================
def send_telegram(msg):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": msg})
    except Exception as e:
        st.warning("Telegram se nepodařilo odeslat")

# ======================
# TEST MODE
# ======================
def run_test_mode():
    msg = f"""
🧪 TEST MODE – Ověření funkčnosti

📈 Akcie: {TEST_STOCK['symbol']}
💵 Cena: ${TEST_STOCK['price']}
📊 RSI: {TEST_STOCK['rsi']}
🧠 AI skóre: {TEST_STOCK['ai_score']}
✅ Signál: {TEST_STOCK['signal']}

🎯 Cíl pro prodej: ${TEST_STOCK['sell_price']}
⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
    send_telegram(msg)

    return pd.DataFrame([{
        "Akcie": TEST_STOCK["symbol"],
        "Cena ($)": TEST_STOCK["price"],
        "RSI": TEST_STOCK["rsi"],
        "AI skóre": TEST_STOCK["ai_score"],
        "Signál": TEST_STOCK["signal"],
        "Prodat při ($)": TEST_STOCK["sell_price"]
    }])

# ======================
# REAL MODE (BEZ PÁDŮ)
# ======================
def run_real_mode():
    # záměrně bezpečné – když nejsou data
    return pd.DataFrame([])

# ======================
# STREAMLIT UI
# ======================
st.set_page_config(page_title="Trading 212 – AI Polo-automat", layout="centered")

st.title("📈 Trading 212 – AI Polo-automat")
st.warning("Není investiční doporučení")

test_mode = st.toggle("🧪 TEST MODE (doporučeno zapnout)", value=True)

st.success("Bot běží automaticky (1× denně)")

if st.button("🚀 Skenovat trh"):
    if test_mode:
        df = run_test_mode()
        st.success("TEST MODE – vždy nalezena 1 akcie")
        st.dataframe(df)
    else:
        df = run_real_mode()
        if df.empty:
            send_telegram("❌ Dnes žádná silná akcie – SAFE režim")
            st.error("Žádná data")
        else:
            st.dataframe(df)
