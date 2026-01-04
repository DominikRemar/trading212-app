import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import os
from datetime import date

# =====================
# KONFIGURACE
# =====================
CAPITAL_CZK = 5000
USD_CZK = 23
MAX_POSITIONS = 2

TICKERS = ["AAPL", "MSFT", "NVDA", "PLTR", "COIN", "META", "GOOGL"]

CONF = {
    "rsi_buy": 40,
    "rsi_sell": 68,
    "take_profit": 0.06,
    "trailing": 0.04
}

STATE_FILE = "positions.csv"
RUN_FILE = "last_run.txt"

# =====================
# TELEGRAM
# =====================
def send_telegram(msg):
    try:
        token = st.secrets["TELEGRAM_TOKEN"]
        chat = st.secrets["TELEGRAM_CHAT_ID"]
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id": chat, "text": msg})
    except:
        pass

# =====================
# INDIKÁTORY
# =====================
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def ai_score(df):
    score = 0
    score += max(0, (50 - df["RSI"].iloc[-1]) * 2)
    score += 10 if df["Close"].iloc[-1] > df["Close"].rolling(20).mean().iloc[-1] else 0
    score += 10 if df["Volume"].iloc[-1] > df["Volume"].mean() else 0
    return int(score)

# =====================
# AUTO RUN (1x DENNĚ)
# =====================
def already_ran_today():
    today = str(date.today())
    if os.path.exists(RUN_FILE):
        if open(RUN_FILE).read() == today:
            return True
    open(RUN_FILE, "w").write(today)
    return False

# =====================
# POZICE
# =====================
def load_positions():
    if os.path.exists(STATE_FILE):
        return pd.read_csv(STATE_FILE)
    return pd.DataFrame(columns=["ticker", "entry", "peak"])

def save_positions(df):
    df.to_csv(STATE_FILE, index=False)

# =====================
# BUY SCAN
# =====================
def scan_market():
    results = []

    for t in TICKERS:
        df = yf.download(t, period="3mo", interval="1d", progress=False)
        if df.empty or len(df) < 30:
            continue

        df["RSI"] = rsi(df["Close"])
        last = df.iloc[-1]

        if last["RSI"] < CONF["rsi_buy"]:
            score = ai_score(df)
            results.append((t, score, last["Close"], last["RSI"]))

    return sorted(results, key=lambda x: x[1], reverse=True)[:MAX_POSITIONS]

# =====================
# SELL MONITOR
# =====================
def check_sell(df_pos):
    updated = []

    for _, row in df_pos.iterrows():
        t = row["ticker"]
        entry = row["entry"]
        peak = row["peak"]

        df = yf.download(t, period="1mo", interval="1d", progress=False)
        if df.empty:
            continue

        df["RSI"] = rsi(df["Close"])
        price = df["Close"].iloc[-1]
        r = df["RSI"].iloc[-1]

        peak = max(peak, price)

        reason = None
        if r > CONF["rsi_sell"]:
            reason = "RSI"
        elif price >= entry * (1 + CONF["take_profit"]):
            reason = "TAKE PROFIT"
        elif price <= peak * (1 - CONF["trailing"]):
            reason = "TRAILING STOP"

        if reason:
            send_telegram(
                f"🔴 SELL ALERT\n\n"
                f"Akcie: {t}\n"
                f"Důvod: {reason}\n"
                f"Cena: {int(price*USD_CZK)} Kč\n"
                f"https://www.trading212.com/trading-instruments/instrument/{t}"
            )
        else:
            updated.append({"ticker": t, "entry": entry, "peak": peak})

    save_positions(pd.DataFrame(updated))

# =====================
# STREAMLIT UI
# =====================
st.set_page_config(page_title="Trading 212 AI Bot")
st.title("🤖 Trading 212 – AI Polo-automat")

if not already_ran_today():
    positions = load_positions()
    check_sell(positions)

    if len(positions) < MAX_POSITIONS:
        picks = scan_market()
        capital_per_stock = CAPITAL_CZK / MAX_POSITIONS

        for t, score, price, r in picks:
            if t not in positions["ticker"].values:
                send_telegram(
                    f"🟢 BUY SIGNAL\n\n"
                    f"Akcie: {t}\n"
                    f"AI skóre: {score}/100\n"
                    f"Cena: {int(price*USD_CZK)} Kč\n"
                    f"RSI: {round(r,1)}\n\n"
                    f"https://www.trading212.com/trading-instruments/instrument/{t}"
                )
                positions = positions.append(
                    {"ticker": t, "entry": price, "peak": price},
                    ignore_index=True
                )

        save_positions(positions)

st.success("✅ Bot běží automaticky (1× denně)")
st.caption("⚠️ Není investiční doporučení. Používáš na vlastní riziko.")
