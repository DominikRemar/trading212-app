import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# ======================
# TELEGRAM (DOSAZENO)
# ======================
TELEGRAM_TOKEN = "8245860410:AAFK59QMTb7r5cY4VcJzqFt46tTh4y45ufM"
TELEGRAM_CHAT_ID = "7772237988"

def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            },
            timeout=10
        )
    except Exception as e:
        print("Telegram error:", e)

# ======================
# WATCHLIST – MICRO / SMALL CAPS
# ======================
WATCHLIST = [
    "GAL.L", "ARCM.L", "KOD.L", "HOC.L",
    "BTG", "GORO", "FSM",
    "UUUU", "DNN", "UEC",
    "ZIM", "GNK"
]

# ======================
# LEVEL 9–10 SCAN
# ======================
def scan():
    results = []

    for t in WATCHLIST:
        try:
            df = yf.Ticker(t).history(period="20d")
            if len(df) < 10:
                continue

            close = df["Close"]
            volume = df["Volume"]

            price_now = close.iloc[-1]
            price_3d = close.iloc[-4]
            price_7d = close.iloc[-8]

            change_3d = (price_now / price_3d - 1) * 100
            change_7d = (price_now / price_7d - 1) * 100

            avg_vol = volume.iloc[:-1].mean()
            vol_now = volume.iloc[-1]
            vol_ratio = vol_now / avg_vol if avg_vol > 0 else 0

            # ----------------------
            # FAKE PUMP FILTER
            # ----------------------
            if change_3d > 60 and vol_ratio < 2:
                continue

            if close.iloc[-1] < close.iloc[-2] * 0.85:
                continue

            # ----------------------
            # SMART MONEY SCORE
            # ----------------------
            score = 0
            if change_7d > 30: score += 25
            if change_7d > 60: score += 15
            if vol_ratio > 2: score += 30
            if vol_ratio > 4: score += 20

            if score < 60:
                continue

            # ----------------------
            # ENTRY LOGIC
            # ----------------------
            last_move = (close.iloc[-1] / close.iloc[-2] - 1) * 100
            entry = "⏳ POČKEJ NA PULLBACK" if last_move > 10 else "✅ VSTUP TEĎ"

            tp1 = round(price_now * 1.2, 2)
            tp2 = round(price_now * 1.4, 2)
            sl = round(price_now * 0.9, 2)

            hold = "⏱ 2–24 h" if vol_ratio > 4 else "⏱ 1–3 dny"

            results.append({
                "Ticker": t,
                "Cena": round(price_now, 2),
                "3D %": round(change_3d, 1),
                "7D %": round(change_7d, 1),
                "Volume x": round(vol_ratio, 1),
                "Skóre": score,
                "Entry": entry,
                "TP1": tp1,
                "TP2": tp2,
                "SL": sl,
                "Hold": hold
            })

        except:
            continue

    return pd.DataFrame(results).sort_values("Skóre", ascending=False)

# ======================
# UI
# ======================
st.set_page_config("LEVEL 9–10 | SMART MONEY AI", layout="centered")
st.title("🔥 LEVEL 9–10 – SMART MONEY EVENT BOT")
st.warning("⚠️ Není investiční doporučení")

st.markdown("""
### Co tenhle bot dělá:
- ❌ filtruje FAKE pumpy
- 🧠 sleduje skutečný tok peněz
- 🎯 hledá přesný vstup (ne vrchol)
- ⏱ cíl: hodiny až max 3 dny
""")

if st.button("🚀 SPUSTIT KOMPLETNÍ ANALÝZU"):
    with st.spinner("Skenuji trh (smart money + volume + pump filter)..."):
        df = scan()

    if df.empty:
        msg = f"""📭 *LEVEL 9–10*
🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}

Žádný kvalitní SMART MONEY setup.
"""
        send_telegram(msg)
        st.info("Teď je lepší čekat.")
        st.code(msg)
    else:
        st.dataframe(df, use_container_width=True)

        msg = f"""🔥 *LEVEL 9–10 SMART MONEY ALERT*
🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}

"""

        for _, r in df.head(3).iterrows():
            msg += (
                f"*{r['Ticker']}*\n"
                f"💰 Cena: {r['Cena']}\n"
                f"📈 7D: {r['7D %']}%\n"
                f"🔊 Volume: {r['Volume x']}x\n"
                f"🎯 Entry: {r['Entry']}\n"
                f"✅ TP1: {r['TP1']} | TP2: {r['TP2']}\n"
                f"🛑 SL: {r['SL']}\n"
                f"{r['Hold']}\n"
                "━━━━━━━━━━━━━━\n"
            )

        send_telegram(msg)
        st.success("📨 Signál odeslán na Telegram")
        st.code(msg)
