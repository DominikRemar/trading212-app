import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# =============================
# TELEGRAM NASTAVENÍ
# =============================
TELEGRAM_TOKEN = "SEM_VLOŽ_BOT_TOKEN"
TELEGRAM_CHAT_ID = "SEM_VLOŽ_CHAT_ID"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
    requests.post(url, data=data)

# =============================
# OBECNÉ NASTAVENÍ
# =============================
KAPITAL_KC = 5000
USD_KC = 23

TICKERS = ["AAPL", "TSLA", "NVDA", "AMD", "META", "PLTR", "COIN"]

st.set_page_config(page_title="Trading 212 – AI Polo-automat", layout="wide")
st.title("📈 Trading 212 – AI Polo-automat")
st.caption("⚠️ Není investiční doporučení")

# =============================
# REŽIM
# =============================
mode = st.selectbox(
    "🧠 Režim",
    ["SAFE", "AGRESIVNÍ"]
)

if mode == "SAFE":
    STOP_LOSS = 0.03
    TAKE_PROFIT = 0.06
else:
    STOP_LOSS = 0.05
    TAKE_PROFIT = 0.10

st.success("✅ Připraveno – klikni na Skenovat trh")

# =============================
# FUNKCE
# =============================
def rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def ai_score(rsi_value, price, avg_price):
    score = 0
    if rsi_value < 30:
        score += 45
    elif rsi_value < 35:
        score += 30
    elif rsi_value < 40:
        score += 15

    if price > avg_price:
        score += 15

    return min(score, 100)

# =============================
# HLAVNÍ LOGIKA
# =============================
if st.button("🚀 Skenovat trh"):
    st.info("🔍 Skenuji trh…")
    results = []

    for t in TICKERS:
        data = yf.download(t, period="2mo", interval="1d", progress=False)
        if data.empty or len(data) < 20:
            continue

        data["RSI"] = rsi(data["Close"])
        last = data.iloc[-1]

        score = ai_score(
            last["RSI"],
            last["Close"],
            data["Close"].mean()
        )

        if score >= 60:
            price_kc = float(last["Close"]) * USD_KC

            results.append({
                "Akcie": t,
                "Cena_KC": round(price_kc, 0),
                "RSI": round(last["RSI"], 1),
                "AI skóre": score
            })

    if not results:
        st.warning("❌ Žádný kvalitní signál (AI filtr)")
        st.stop()

    df = pd.DataFrame(results).sort_values("AI skóre", ascending=False).head(2)
    investice = int(KAPITAL_KC / len(df))

    st.subheader("🔥 AI výběr")

    for _, row in df.iterrows():
        sl = round(row["Cena_KC"] * (1 - STOP_LOSS), 0)
        tp = round(row["Cena_KC"] * (1 + TAKE_PROFIT), 0)

        st.markdown(f"""
### 🟢 {row['Akcie']}
🤖 **AI skóre:** {row['AI skóre']} / 100  
💰 **Investuj:** {investice} Kč  
📉 **Stop-loss:** {sl} Kč  
📈 **Take-profit:** {tp} Kč  

📲 👉 [Otevřít v Trading 212](trading212://instrument/{row['Akcie']})
""")

        # SEND BUY ALERT
        send_telegram(
            f"🟢 KOUPIT {row['Akcie']}\n"
            f"AI skóre: {row['AI skóre']}\n"
            f"Investice: {investice} Kč\n"
            f"SL: {sl} Kč | TP: {tp} Kč"
        )

        # =============================
        # HLÍDÁNÍ PRODEJE
        # =============================
        current = st.number_input(
            f"Aktuální cena {row['Akcie']} (Kč)",
            value=float(row["Cena_KC"]),
            key=row["Akcie"]
        )

        if current <= sl:
            st.error("🔴 STOP-LOSS → PRODAT")
            send_telegram(f"🔴 PRODAT {row['Akcie']} – STOP-LOSS")
        elif current >= tp:
            st.success("🟢 TAKE-PROFIT → PRODAT")
            send_telegram(f"🟢 PRODAT {row['Akcie']} – TAKE-PROFIT")
        else:
            st.info("⏳ Drž pozici")

st.caption("Používáš na vlastní riziko")
