import streamlit as st
import yfinance as yf
import pandas as pd

# =============================
# ZÁKLADNÍ NASTAVENÍ
# =============================
KAPITAL_KC = 5000
USD_KC = 23

TICKERS = ["AAPL", "TSLA", "NVDA", "AMD", "META", "PLTR", "COIN"]

st.set_page_config(page_title="Trading 212 Polo-automat", layout="wide")
st.title("📈 Trading 212 – Polo-automat")
st.caption("⚠️ Není investiční doporučení")

# =============================
# REŽIM
# =============================
mode = st.selectbox(
    "🧠 Zvol režim",
    ["SAFE (nižší riziko)", "AGRESIVNÍ (rychlé obchody)"]
)

if "SAFE" in mode:
    STOP_LOSS = 0.03
    TAKE_PROFIT = 0.06
else:
    STOP_LOSS = 0.05
    TAKE_PROFIT = 0.10

st.success("✅ Aplikace připravena – klikni na Skenovat trh")

# =============================
# FUNKCE
# =============================
def rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = gain.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

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

        # Jednoduchá AI logika
        score = 0
        if last["RSI"] < 35:
            score += 2
        if last["Close"] > data["Close"].mean():
            score += 1

        if score >= 2:
            price_usd = float(last["Close"])
            price_kc = price_usd * USD_KC

            results.append({
                "Akcie": t,
                "Cena_KC": round(price_kc, 0),
                "RSI": round(last["RSI"], 1),
                "Score": score
            })

    if not results:
        st.error("❌ Teď není bezpečný vstup – čekej")
        st.stop()

    df = pd.DataFrame(results).sort_values("RSI").head(2)
    investice = int(KAPITAL_KC / len(df))

    st.subheader("🔥 Doporučené akcie")

    for _, row in df.iterrows():
        sl = round(row["Cena_KC"] * (1 - STOP_LOSS), 0)
        tp = round(row["Cena_KC"] * (1 + TAKE_PROFIT), 0)

        st.markdown(f"""
### 🟢 {row['Akcie']}
💰 **Investuj:** {investice} Kč  
📉 **Stop-loss:** {sl} Kč  
📈 **Take-profit:** {tp} Kč  

📲 **Trading 212:**  
👉 [Otevřít v Trading 212](trading212://instrument/{row['Akcie']})
""")

        # =============================
        # ALERT – HLÍDÁNÍ PRODEJE
        # =============================
        current = st.number_input(
            f"Aktuální cena {row['Akcie']} (Kč)",
            value=float(row["Cena_KC"]),
            key=row["Akcie"]
        )

        if current <= sl:
            st.error("🔴 STOP-LOSS ZASAŽEN → PRODAT IHNED")
        elif current >= tp:
            st.success("🟢 TAKE-PROFIT → PRODAT A ZAMKNOUT ZISK")
        else:
            st.info("⏳ Drž pozici – žádný signál k prodeji")

st.caption("Používáš na vlastní riziko")
