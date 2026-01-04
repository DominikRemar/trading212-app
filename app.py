import streamlit as st
import pandas as pd

st.set_page_config(page_title="Trading 212 Scanner", page_icon="📈")

st.title("📈 Trading 212 – Rychlý výdělek")
st.success("✅ Aplikace připravena. Klikni na Skenovat trh")
st.caption("⚠️ Není investiční doporučení. Používáš na vlastní riziko.")

KAPITAL_EUR = 500
USD_EUR = 0.92

TICKERS = ["AAPL", "TSLA", "NVDA", "AMD", "META", "PLTR", "SOFI", "COIN"]

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

if st.button("🚀 Skenovat trh"):
    import yfinance as yf

    results = []

    with st.spinner("🔍 Skenuji trh..."):
        for t in TICKERS:
            data = yf.download(t, period="1mo", interval="1d", progress=False)

            if data.empty or len(data) < 20:
                continue

            data["RSI"] = rsi(data["Close"])
            last = data.iloc[-1]

            price = float(last["Close"])
            rsi_val = float(last["RSI"])

            # REALISTICKÉ PODMÍNKY
            if rsi_val < 45:
                signal = "🟢 KOUPIT"
            elif rsi_val > 65:
                signal = "🔴 PRODAT"
            else:
                signal = "🟡 SLEDOVAT"

            results.append({
                "Akcie": t,
                "Cena ($)": round(price, 2),
                "Cena (€)": round(price * USD_EUR, 2),
                "RSI": round(rsi_val, 1),
                "Signál": signal
            })

    df = pd.DataFrame(results)

    if df.empty:
        st.warning("❌ Data nedostupná")
    else:
        # TOP 3 příležitosti
        buy_df = df[df["Signál"] == "🟢 KOUPIT"].sort_values("RSI").head(3)

        sell_df = df[df["Signál"] == "🔴 PRODAT"]

        if not buy_df.empty:
            st.subheader("🔥 TOP 3 ke koupi")
            st.dataframe(buy_df, use_container_width=True)

        if not sell_df.empty:
            st.subheader("⚠️ Zvážit prodej")
            st.dataframe(sell_df, use_container_width=True)

        if buy_df.empty and sell_df.empty:
            st.info("ℹ️ Trh je neutrální – žádný silný signál")
