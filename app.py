import streamlit as st
import pandas as pd
import numpy as np
import time

# ---------- NASTAVENÍ ----------
KAPITAL = 5000
MAX_AKCII = 2
STOP_LOSS_PCT = 0.04
TAKE_PROFIT_PCT = 0.07

AKCIE = [
    {"ticker": "AAPL", "price": 249, "rsi": 31},
    {"ticker": "MSFT", "price": 410, "rsi": 38},
    {"ticker": "COIN", "price": 218, "rsi": 28},
    {"ticker": "PLTR", "price": 154, "rsi": 34},
    {"ticker": "NVDA", "price": 610, "rsi": 42},
]

# ---------- AI SKÓRE ----------
def ai_score(rsi):
    score = 0
    if rsi < 30:
        score += 40
    elif rsi < 35:
        score += 25
    elif rsi < 40:
        score += 10
    score += 30  # kvalita firmy (simulace)
    return min(score, 100)

# ---------- UI ----------
st.set_page_config(page_title="Trading 212 – AI režim", layout="centered")
st.title("📈 Trading 212 – AI Ultra Safe")
st.success("Aplikace připravena. Klikni na **Skenovat trh**")

st.warning("Není investiční doporučení. Používáš na vlastní riziko.")

if st.button("🚀 Skenovat trh"):
    with st.spinner("🔍 Skenuji trh... vydrž pár sekund"):
        time.sleep(1.5)

        data = []
        for a in AKCIE:
            score = ai_score(a["rsi"])
            if score >= 60:
                data.append({
                    "Akcie": a["ticker"],
                    "Cena (€)": a["price"],
                    "RSI": a["rsi"],
                    "AI skóre": score
                })

        if not data:
            st.error("❌ Nic vhodného nenalezeno (AI filtr)")
        else:
            df = pd.DataFrame(data).sort_values("AI skóre", ascending=False).head(MAX_AKCII)

            investice_na_akcii = KAPITAL / len(df)

            df["Investice (Kč)"] = int(investice_na_akcii)
            df["Stop-loss (Kč)"] = (investice_na_akcii * (1 - STOP_LOSS_PCT)).astype(int)
            df["Take-profit (Kč)"] = (investice_na_akcii * (1 + TAKE_PROFIT_PCT)).astype(int)
            df["Signál"] = "🟢 KOUPIT"

            st.subheader("🔥 AI výběr (Ultra safe)")
            st.dataframe(df, use_container_width=True)

            st.info(
                f"📌 Kapitál {KAPITAL} Kč rozdělen mezi {len(df)} akcie\n\n"
                f"🛑 Max ztráta na obchod: ~{int(investice_na_akcii * STOP_LOSS_PCT)} Kč\n"
                f"🎯 Cíl zisku: ~{int(investice_na_akcii * TAKE_PROFIT_PCT)} Kč"
            )
