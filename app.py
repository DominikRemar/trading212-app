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
# NASTAVENÍ
# ======================
STOCKS = ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AMD","NFLX","INTC"]
TAKE_PROFIT = 1.10   # +10 %
STOP_LOSS = 0.95     # -5 %

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
# SCAN TRHU
# ======================
def scan_market():
    results = []

    for symbol in STOCKS:
        try:
            data = yf.download(symbol, period="1y", interval="1d", progress=False)
            if len(data) < 250:
                continue

            close = data["Close"]
            price = float(close.iloc[-1])

            rsi = compute_rsi(close).iloc[-1]
            ma200 = close.rolling(200).mean().iloc[-1]

            # Trend filtr
            if price < ma200:
                continue

            change_30d = ((close.iloc[-1] - close.iloc[-21]) / close.iloc[-21]) * 100

            score = 0
            if 30 <= rsi <= 50:
                score += 40
            if change_30d > 0:
                score += 30
            if change_30d > 5:
                score += 20

            if score < 40:
                continue

            results.append({
                "Akcie": symbol,
                "Cena ($)": round(price, 2),
                "RSI": round(rsi, 1),
                "30d %": round(change_30d, 1),
                "AI skóre": score,
                "Take Profit ($)": round(price * TAKE_PROFIT, 2),
                "Stop Loss ($)": round(price * STOP_LOSS, 2)
            })

        except:
            continue

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results).sort_values("AI skóre", ascending=False).head(3)

# ======================
# UI
# ======================
st.set_page_config("Trading 212 – AI Asistent", layout="centered")
st.title("📈 Trading 212 – AI Asistent")
st.warning("⚠️ Není investiční doporučení")

if st.button("🚀 Skenovat trh"):
    df = scan_market()

    if df.empty:
        st.error("❌ Dnes žádná vhodná akcie")
        send_telegram("❌ Dnes nebyla nalezena žádná vhodná akcie")
        st.stop()

    st.success("✅ Nalezeny TOP obchodní příležitosti")
    st.dataframe(df, use_container_width=True)

    # ======================
    # TELEGRAM ZPRÁVA
    # ======================
    msg = "📊 *TRADING 212 – DENNÍ SIGNÁLY*\n"
    msg += "━━━━━━━━━━━━━━━━━━\n\n"

    best_score = df["AI skóre"].max()

    for i, row in enumerate(df.itertuples(), start=1):
        rr = round(
            (row._6 - row._2) / (row._2 - row._7), 2
        )

        badge = " ⭐ *BEST*" if row._5 == best_score else ""

        msg += (
            f"*{i}. {row._1}* 📈{badge}\n"
            f"🟢 *BUY:* `${row._2}`\n"
            f"🎯 *TAKE PROFIT:* `${row._6}`\n"
            f"🛑 *STOP LOSS:* `${row._7}`\n"
            f"📉 RSI: `{row._3}` | 📊 30d: `{row._4}%`\n"
            f"🧠 Skóre: `{row._5}` | ⚖️ R:R: `{rr}`\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
        )

    msg += (
        "📌 *Postup:*\n"
        "1️⃣ BUY za market cenu\n"
        "2️⃣ Nastav STOP LOSS\n"
        "3️⃣ Nastav TAKE PROFIT\n\n"
        "⚠️ *Není investiční doporučení*"
    )

    send_telegram(msg)
