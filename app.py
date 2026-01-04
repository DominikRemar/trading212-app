import streamlit as st
import pandas as pd
import requests
import yfinance as yf
from datetime import datetime

# ======================
# TELEGRAM – TVÉ ÚDAJE
# ======================
TELEGRAM_TOKEN = "8245860410:AAFK59QMTb7r5cY4VcJzqFt46tTh4y45ufM"
TELEGRAM_CHAT_ID = "7772237988"

# ======================
# NASTAVENÍ
# ======================
STOCKS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",
    "META", "TSLA", "AMD", "NFLX", "INTC"
]

# ======================
# TOOLS
# ======================
def trading212_link(symbol):
    return f"https://www.trading212.com/trading-instruments/instrument-details?instrumentId={symbol}"

def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(
            url,
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

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ======================
# REAL SCAN – FUNKČNÍ
# ======================
def scan_market():
    candidates = []

    for symbol in STOCKS:
        try:
            data = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if len(data) < 60:
                continue

            close = data["Close"]
            price = float(close.iloc[-1])
            rsi = compute_rsi(close).iloc[-1]

            # růst za poslední měsíc
            change_30d = ((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100

            # AI skóre (momentum + zdravé RSI)
            ai_score = (change_30d * 3) + (70 - abs(60 - rsi)) * 2

            if change_30d > 3 and ai_score >= 60:
                candidates.append({
                    "Akcie": symbol,
                    "Cena ($)": round(price, 2),
                    "RSI": round(rsi, 1),
                    "AI skóre": int(ai_score),
                    "Signál": "KUPIT",
                    "Prodat při ($)": round(price * 1.10, 2)
                })

        except:
            pass

    if not candidates:
        return pd.DataFrame()

    df = pd.DataFrame(candidates)
    return df.sort_values("AI skóre", ascending=False).head(1)

# ======================
# STREAMLIT UI
# ======================
st.set_page_config(page_title="Trading 212 – AI Polo-automat", layout="centered")

st.title("📈 Trading 212 – AI Polo-automat")
st.warning("⚠️ Není investiční doporučení")

TEST_MODE = st.toggle("🧪 TEST MODE (doporučeno)", value=True)

if st.button("🚀 Skenovat trh"):

    if TEST_MODE:
        df = pd.DataFrame([{
            "Akcie": "AAPL",
            "Cena ($)": 190.0,
            "RSI": 42.0,
            "AI skóre": 82,
            "Signál": "KUPIT",
            "Prodat při ($)": 215.0
        }])

        link = trading212_link("AAPL")

        send_telegram(
            f"""🧪 *TEST MODE – BUY SIGNÁL*

📈 Akcie: AAPL
💰 Cena: $190
📉 RSI: 42
🧠 AI skóre: 82
✅ Signál: KUPIT

🎯 Cíl: $215

👉 [📈 Otevřít v Trading 212]({link})"""
        )

        st.success("TEST MODE – vždy nalezena 1 akcie")

    else:
        df = scan_market()

        if df.empty:
            st.error("❌ Dnes žádná silná akcie – SAFE režim")
            send_telegram("❌ Dnes žádná silná akcie – SAFE režim")
            st.stop()

        stock = df.iloc[0]
        link = trading212_link(stock["Akcie"])

        send_telegram(
            f"""📊 *Trading212 AI – BUY SIGNÁL*

📈 Akcie: {stock['Akcie']}
💰 Cena: ${stock['Cena ($)']}
📉 RSI: {stock['RSI']}
🧠 AI skóre: {stock['AI skóre']}
✅ Signál: KUPIT

🎯 Cíl: ${stock['Prodat při ($)']}

👉 [📈 Otevřít v Trading 212]({link})"""
        )

        st.success("✅ Nalezena silná akcie")

    st.dataframe(df, use_container_width=True)
    st.markdown(f"👉 **[Otevřít v Trading 212]({trading212_link(df.iloc[0]['Akcie'])})**")
