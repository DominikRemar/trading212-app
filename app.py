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
    return f"https://www.trading212.com/trading-instruments/instruments/search?query={symbol}"


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
# SCAN
# ======================
def scan_market():
    results = []

    for symbol in STOCKS:
        try:
            data = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if len(data) < 60:
                continue

            close = data["Close"]
            price = float(close.iloc[-1])
            rsi = compute_rsi(close).iloc[-1]
            change_30d = ((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100

            ai_score = int((change_30d * 3) + (70 - abs(60 - rsi)) * 2)

            results.append({
                "Akcie": symbol,
                "Cena ($)": round(price, 2),
                "RSI": round(rsi, 1),
                "Změna 30d %": round(change_30d, 1),
                "AI skóre": ai_score,
                "Prodat při ($)": round(price * 1.10, 2),
            })

        except:
            continue

    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)

    # preferuj silné, ale KDYŽ NEJSOU, vezmi nejlepší slabší
    df = df.sort_values("AI skóre", ascending=False)

    return df.head(1)

# ======================
# STREAMLIT UI
# ======================
st.set_page_config(page_title="Trading 212 – AI Asistent", layout="centered")

st.title("📈 Trading 212 – AI Asistent")
st.warning("⚠️ Není investiční doporučení")

TEST_MODE = st.toggle("🧪 TEST MODE", value=False)

if st.button("🚀 Skenovat trh"):

    if TEST_MODE:
        df = pd.DataFrame([{
            "Akcie": "AAPL",
            "Cena ($)": 190.0,
            "RSI": 45.0,
            "Změna 30d %": 4.2,
            "AI skóre": 78,
            "Prodat při ($)": 209.0
        }])
    else:
        df = scan_market()

    if df.empty:
        st.error("❌ Trh dnes nedává ani slabý signál")
        send_telegram("❌ Dnes žádná vhodná akcie")
        st.stop()

    stock = df.iloc[0]
    link = trading212_link(stock["Akcie"])

    strength = "🟢 SILNÝ" if stock["AI skóre"] >= 70 else "🟡 SLABŠÍ – NA RIZIKO"

    send_telegram(
        f"""📊 *Trading 212 – AI Signál*

📈 Akcie: {stock['Akcie']}
💰 Cena: ${stock['Cena ($)']}
📉 RSI: {stock['RSI']}
📊 30d změna: {stock['Změna 30d %']} %
🧠 AI skóre: {stock['AI skóre']}
⚠️ Hodnocení: {strength}

🎯 Doporučený cíl: ${stock['Prodat při ($)']}

👉 [Otevřít v Trading 212]({link})

📌 Nastav LIMIT SELL na cílovou cenu
"""
    )

    st.success("✅ Akcie nalezena")
    st.dataframe(df, use_container_width=True)
    st.markdown(f"👉 **[Otevřít v Trading 212]({link})**")

    # UPOZORNĚNÍ BLÍŽÍCÍ SE CÍL
    if stock["Cena ($)"] >= stock["Prodat při ($)"] * 0.9:
        send_telegram(
            f"⏰ *POZOR!* {stock['Akcie']} je blízko cíle ({stock['Prodat při ($)']}$)"
        )
