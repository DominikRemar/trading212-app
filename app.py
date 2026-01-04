import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from datetime import datetime

# ======================
# TELEGRAM
# ======================
TELEGRAM_TOKEN = "8245860410:AAFK59QMTb7r5cY4VcJzqFt46tTh4y45ufM"
TELEGRAM_CHAT_ID = "7772237988"

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

# ======================
# NASTAVENÍ
# ======================
STOCKS = ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AMD","NFLX","INTC"]
BUDGET_CZK = 5000

MODES = {
    "Konzervativní 🟢": {"tp":1.06, "sl":0.97, "rsi":(35,55)},
    "Vyvážený 🟡": {"tp":1.10, "sl":0.95, "rsi":(30,60)},
    "Agresivní 🔴": {"tp":1.15, "sl":0.92, "rsi":(25,70)},
}

# ======================
# INDIKÁTORY
# ======================
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ======================
# AI SCAN
# ======================
def scan_market(mode):
    results = []

    for symbol in STOCKS:
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="6mo")

            if len(data) < 60:
                continue

            close = data["Close"]
            price = float(close.iloc[-1])
            rsi = compute_rsi(close).iloc[-1]
            ma200 = close.rolling(200).mean().iloc[-1]
            change_30d = ((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100

            info = stock.info
            target = info.get("targetMeanPrice")
            rec = info.get("recommendationKey")

            score = 0
            if price > ma200: score += 25
            if mode["rsi"][0] <= rsi <= mode["rsi"][1]: score += 20
            if change_30d > 0: score += 15
            if target and target > price: score += 20
            if rec in ["buy","strong_buy"]: score += 20
            elif rec == "hold": score += 10

            results.append({
                "Akcie": symbol,
                "Cena": round(price,2),
                "RSI": round(rsi,1),
                "30d %": round(change_30d,1),
                "Target": round(target,2) if target else "N/A",
                "AI skóre": score,
                "TP": round(price * mode["tp"],2),
                "SL": round(price * mode["sl"],2),
                "Trailing SL": round(price * (mode["sl"] + 0.02),2)
            })

        except:
            continue

    return pd.DataFrame(results).sort_values("AI skóre", ascending=False).head(3)

# ======================
# UI
# ======================
st.set_page_config("Trading 212 – AI Asistent", layout="centered")
st.title("📈 Trading 212 – AI Asistent")
st.warning("⚠️ Není investiční doporučení")

mode_name = st.selectbox("🧠 Vyber obchodní mód", list(MODES.keys()))

if st.button("🚀 Skenovat trh"):
    df = scan_market(MODES[mode_name])

    if df.empty:
        st.error("❌ Dnes žádné signály")
        send_telegram("❌ Dnes žádné vhodné signály")
        st.stop()

    st.dataframe(df, use_container_width=True)

    budget_per_trade = int(BUDGET_CZK / len(df))
    best = df["AI skóre"].max()

    msg = f"📊 *AI SIGNÁLY – {mode_name}*\n"
    msg += f"📅 {datetime.now().strftime('%d.%m.%Y')}\n"
    msg += f"💰 Rozpočet: {BUDGET_CZK} Kč\n"
    msg += f"➡️ Na akcii: {budget_per_trade} Kč\n"
    msg += "━━━━━━━━━━━━━━━━━━\n\n"

    for i,row in enumerate(df.itertuples(),1):
        badge = " ⭐ *BEST*" if row._6 == best else ""
        msg += (
            f"*{i}. {row._1}*{badge}\n"
            f"🟢 BUY: `${row._2}`\n"
            f"🛑 STOP: `${row._8}`\n"
            f"🎯 LIMIT: `${row._7}`\n"
            f"🔒 Trailing SL: `${row._9}`\n"
            f"📉 RSI: {row._3} | 📊 30d: {row._4}%\n"
            f"🧠 Skóre: {row._6}\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
        )

    msg += (
        "📌 *Jak obchodovat v Trading 212:*\n"
        "1️⃣ Nakup Market\n"
        "2️⃣ Nastav Stop-Loss\n"
        "3️⃣ Nastav Limit Sell\n"
        "4️⃣ Při růstu posouvej STOP (Trailing)\n\n"
        "⚠️ Není investiční doporučení"
    )

    send_telegram(msg)
