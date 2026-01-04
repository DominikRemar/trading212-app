import streamlit as st
import pandas as pd
import requests
import yfinance as yf

# ======================
# TELEGRAM
# ======================
TELEGRAM_TOKEN = "8245860410:AAFK59QMTb7r5cY4VcJzqFt46tTh4y45ufM"
TELEGRAM_CHAT_ID = "7772237988"

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

# ======================
# DATA
# ======================
STOCKS = ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AMD","NFLX","INTC"]

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

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
                "30d %": round(change_30d, 1),
                "AI skóre": ai_score,
                "Cíl ($)": round(price * 1.10, 2)
            })
        except:
            pass

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results).sort_values("AI skóre", ascending=False).head(1)

# ======================
# UI
# ======================
st.set_page_config("Trading 212 – AI Asistent", layout="centered")
st.title("📈 Trading 212 – AI Asistent")
st.warning("⚠️ Není investiční doporučení")

if st.button("🚀 Skenovat trh"):
    df = scan_market()

    if df.empty:
        st.error("❌ Žádná akcie nenalezena")
        send_telegram("❌ Dnes žádná vhodná akcie")
        st.stop()

    stock = df.iloc[0]
    strength = "🟢 SILNÉ" if stock["AI skóre"] >= 70 else "🟡 SLABŠÍ – NA RIZIKO"

    send_telegram(
        f"""📊 *Trading 212 – AI ANALÝZA*

📈 Akcie: {stock['Akcie']}
💰 Cena: ${stock['Cena ($)']}
📉 RSI: {stock['RSI']}
📊 30d změna: {stock['30d %']} %
🧠 AI skóre: {stock['AI skóre']}
⚠️ Hodnocení: {strength}

🎯 Doporučený cíl: ${stock['Cíl ($)']}

📌 Otevři Trading 212 a vyhledej ticker: *{stock['Akcie']}*
📌 Nastav LIMIT SELL na cílovou cenu
"""
    )

    st.success("✅ Akcie nalezena – info odesláno do Telegramu")
    st.dataframe(df, use_container_width=True)

    st.markdown(
        "👉 **Otevři Trading 212 a vyhledej ticker ručně**  \n"
        f"🔎 **Ticker:** `{stock['Akcie']}`"
    )
