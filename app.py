import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import yfinance as yf

# ======================
# KONFIGURACE
# ======================
TEST_STOCK = {
    "symbol": "AAPL",
    "price": 190.0,
    "rsi": 42.0,
    "ai_score": 82,
    "signal": "KUPIT",
    "sell_price": 215.0,
    "sell_after_hours": 24
}

# ======================
# TRADING 212 LINK
# ======================
def trading212_link(symbol):
    return f"https://www.trading212.com/trading-instruments/instrument-details?instrumentId={symbol}"

# ======================
# TELEGRAM
# ======================
def send_telegram(msg):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": msg,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
        )
    except Exception:
        st.warning("Telegram se nepodařilo odeslat")

# ======================
# SESSION STATE
# ======================
if "open_trade" not in st.session_state:
    st.session_state.open_trade = None

# ======================
# ZÍSKÁNÍ AKTUÁLNÍ CENY
# ======================
def get_current_price(symbol):
    try:
        data = yf.download(symbol, period="1d", interval="1m", progress=False)
        return float(data["Close"].iloc[-1])
    except Exception:
        return None

# ======================
# BUY – TEST MODE
# ======================
def run_test_mode():
    link = trading212_link(TEST_STOCK["symbol"])
    sell_time = datetime.now() + timedelta(hours=TEST_STOCK["sell_after_hours"])

    st.session_state.open_trade = {
        "symbol": TEST_STOCK["symbol"],
        "sell_price": TEST_STOCK["sell_price"],
        "sell_time": sell_time
    }

    msg = f"""
🧪 *TEST MODE – BUY SIGNÁL*

📈 *Akcie:* {TEST_STOCK['symbol']}
💵 *Cena:* ${TEST_STOCK['price']}
📊 *RSI:* {TEST_STOCK['rsi']}
🧠 *AI skóre:* {TEST_STOCK['ai_score']}
✅ *Signál:* KUPIT

🎯 *Prodat při:* ${TEST_STOCK['sell_price']}
⏰ *Nejpozději:* {sell_time.strftime('%d.%m.%Y %H:%M')}

👉 [📈 Otevřít v Trading 212]({link})
"""
    send_telegram(msg)

    return pd.DataFrame([{
        "Akcie": TEST_STOCK["symbol"],
        "Cena ($)": TEST_STOCK["price"],
        "RSI": TEST_STOCK["rsi"],
        "AI skóre": TEST_STOCK["ai_score"],
        "Signál": "KUPIT",
        "Prodat při ($)": TEST_STOCK["sell_price"]
    }])

# ======================
# KONTROLA PRODEJE (CENA / ČAS)
# ======================
def check_sell_condition():
    trade = st.session_state.open_trade
    if not trade:
        return

    now = datetime.now()
    current_price = get_current_price(trade["symbol"])

    reason = None
    if current_price and current_price >= trade["sell_price"]:
        reason = f"CENA DOSAŽENA (${current_price:.2f})"
    elif now >= trade["sell_time"]:
        reason = "VYPRŠEL ČAS"

    if reason:
        link = trading212_link(trade["symbol"])
        msg = f"""
🚨 *JE ČAS PRODAT!*

📉 *Akcie:* {trade['symbol']}
📌 *Důvod:* {reason}
🎯 *Cíl:* ${trade['sell_price']}

👉 [📉 Prodat v Trading 212]({link})
"""
        send_telegram(msg)
        st.session_state.open_trade = None
        st.success("🔔 Odesláno SELL upozornění")

# ======================
# STREAMLIT UI
# ======================
st.set_page_config(
    page_title="Trading 212 – AI Polo-automat",
    layout="centered"
)

st.title("📈 Trading 212 – AI Polo-automat")
st.warning("⚠️ Není investiční doporučení")

test_mode = st.toggle("🧪 TEST MODE (doporučeno)", value=True)

# kontrola při každém načtení
check_sell_condition()

if st.button("🚀 Skenovat trh"):
    if test_mode:
        df = run_test_mode()
        st.success("TEST MODE – BUY signál odeslán")
        st.dataframe(df, use_container_width=True)

        st.markdown(
            f"👉 **[📈 Otevřít {TEST_STOCK['symbol']} v Trading 212]({trading212_link(TEST_STOCK['symbol'])})**"
        )
