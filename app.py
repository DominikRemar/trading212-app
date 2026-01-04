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
    # SPRÁVNÝ ODKAZ – vyhledávání (funguje vždy)
    return f"https://www.trading212.com/search?query={symbol}"

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
# SCAN TRHU – VŽDY NAJDE 1 AKCII
# ======================
def scan_market():
    strong = []
    fallback = []

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

            row = {
                "Akcie": symbol,
                "Cena ($)": round(price, 2),
                "RSI": round(rsi, 1),
                "30d %": round(change_30d, 2),
                "AI skóre": int(ai_score),
                "Prodat při ($)": round(price * 1.10, 2)
            }

            if change_30d > 3 and ai_score >= 70:
                row["Signál"] = "🟢 KUPIT – SILNÝ SIGNÁL"
                strong.append(row)
            else:
                row["Signál"] = "⚠️ SLABŠÍ SIGNÁL – RIZIKO"
                fallback.append(row)

        except:
            pass

    if strong:
        return pd.DataFrame(strong).sort_values("AI skóre", ascending=False).head(1)

    # fallback – vždy aspoň 1 akcie
    return pd.DataFrame(fallback).sort_values("AI skóre", ascending=False).head(1)

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
            "Akcie": "NVDA",
            "Cena ($)": 188.85,
            "RSI": 59.3,
            "30d %": 5.16,
            "AI skóre": 154,
            "Signál": "🟢 KUPIT – SILNÝ SIGNÁL",
            "Prodat při ($)": 207.74
        }])
        stock = df.iloc[0]

    else:
        df = scan_market()
        stock = df.iloc[0]

    link = trading212_link(stock["Akcie"])

    risk_note = (
        "🟢 Silné AI hodnocení"
        if "SILNÝ" in stock["Signál"]
        else "🟡 Slabší AI hodnocení – rozhodnutí je na tobě"
    )

    send_telegram(
        f"""📊 *Trading212 AI – ANALÝZA*

📈 Akcie: {stock['Akcie']}
💰 Cena: ${stock['Cena ($)']}
📉 RSI: {stock['RSI']}
📈 30d změna: {stock['30d %']} %
🧠 AI skóre: {stock['AI skóre']}
{risk_note}

🎯 Cíl: ${stock['Prodat při ($)']}

👉 [📈 Otevřít v Trading 212]({link})"""
    )

    st.success("✅ Analýza hotová")
    st.dataframe(df, use_container_width=True)
    st.markdown(f"👉 **[Otevřít v Trading 212]({link})**")
