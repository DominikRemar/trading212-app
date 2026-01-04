import streamlit as st
import pandas as pd
import requests
import yfinance as yf

# ======================
# TELEGRAM – TVÉ ÚDAJE
# ======================
TELEGRAM_TOKEN = "8245860410:AAFK59QMTb7r5cY4VcJzqFt46tTh4y45ufM"
TELEGRAM_CHAT_ID = "7772237988"

# ======================
# WATCHLIST
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
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
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
# MARKET SCAN – ALWAYS 1 STOCK
# ======================
def scan_market():
    rows = []

    for symbol in STOCKS:
        try:
            data = yf.download(symbol, period="6mo", interval="1d", progress=False)
            if len(data) < 60:
                continue

            close = data["Close"]
            price = float(close.iloc[-1])
            rsi = compute_rsi(close).iloc[-1]
            change_30d = ((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100

            ai_score = (change_30d * 3) + (70 - abs(60 - rsi)) * 2

            rows.append({
                "Akcie": symbol,
                "Cena ($)": round(price, 2),
                "RSI": round(rsi, 1),
                "30d %": round(change_30d, 2),
                "AI skóre": int(ai_score)
            })

        except:
            pass

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # vždy vezmeme nejlepší
    best = df.sort_values("AI skóre", ascending=False).head(1).copy()

    score = best.iloc[0]["AI skóre"]
    change = best.iloc[0]["30d %"]

    if score >= 60 and change > 3:
        signal = "KUPIT – SILNÝ SIGNÁL"
        note = "🟢 Silné AI hodnocení"
    else:
        signal = "KUPIT – RIZIKO"
        note = "⚠️ Slabší AI hodnocení – rozhodnutí je na tobě"

    best["Signál"] = signal
    best["Poznámka AI"] = note
    best["Prodat při ($)"] = round(best.iloc[0]["Cena ($)"] * 1.10, 2)

    return best

# ======================
# STREAMLIT UI
# ======================
st.set_page_config(page_title="Trading 212 – AI Polo-automat", layout="centered")

st.title("📈 Trading 212 – AI Polo-automat")
st.warning("⚠️ Není investiční doporučení")

TEST_MODE = st.toggle("🧪 TEST MODE", value=True)

if st.button("🚀 Skenovat trh"):

    if TEST_MODE:
        df = pd.DataFrame([{
            "Akcie": "AAPL",
            "Cena ($)": 190.0,
            "RSI": 42.0,
            "AI skóre": 82,
            "Signál": "KUPIT – SILNÝ SIGNÁL",
            "Poznámka AI": "🟢 Silné AI hodnocení",
            "Prodat při ($)": 215.0
        }])

        link = trading212_link("AAPL")

        send_telegram(
            f"""🧪 *TEST MODE – BUY SIGNÁL*

📈 Akcie: AAPL
💰 Cena: $190
🧠 AI skóre: 82
🟢 Silné hodnocení

👉 [📈 Otevřít v Trading 212]({link})"""
        )

        st.success("TEST MODE – OK")

    else:
        df = scan_market()

        stock = df.iloc[0]
        link = trading212_link(stock["Akcie"])

        send_telegram(
            f"""📊 *Trading212 AI – ANALÝZA*

📈 Akcie: {stock['Akcie']}
💰 Cena: ${stock['Cena ($)']}
📉 RSI: {stock['RSI']}
🧠 AI skóre: {stock['AI skóre']}
📌 {stock['Poznámka AI']}

🎯 Cíl: ${stock['Prodat při ($)']}

👉 [📈 Otevřít v Trading 212]({link})"""
        )

        st.success("✅ Vybrána nejlepší dostupná akcie")

    st.dataframe(df, use_container_width=True)
    st.markdown(f"👉 **[Otevřít v Trading 212]({trading212_link(df.iloc[0]['Akcie'])})**")
