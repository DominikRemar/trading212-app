import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import feedparser
from textblob import TextBlob

# Nastavení titulku aplikace
st.set_page_config(page_title="Stock Signály", layout="wide")
st.title("Sledování akcií (Trading 212) pro krátkodobé signály")

# Vstup od uživatele: tickery a rozpočet
tickers_input = st.text_input("Ticker(y) oddělené čárkou (např. AAPL, MSFT, GOOGL):", "AAPL, MSFT, GOOGL")
budget = st.number_input("Celkový rozpočet (EUR):", min_value=0.0, value=500.0, step=50.0)

if tickers_input:
    tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
    results = []
    for ticker in tickers:
        # Stáhnout historická data
        try:
            data = yf.download(ticker, period="6mo", interval="1d", progress=False)
        except Exception:
            continue
        if data is None or data.empty:
            continue

        # Výpočet RSI hodnoty
        delta = data['Close'].diff(1)
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        window = 14
        if len(data) < window:
            continue
        avg_gain = gain.ewm(span=window, adjust=False).mean()
        avg_loss = loss.ewm(span=window, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi_series = 100 - (100 / (1 + rs))
        last_rsi = rsi_series.iloc[-1] if not rsi_series.empty else None

        cena = data['Close'].iloc[-1]  # aktuální cena (EUR)

        # Google News RSS - sestavení URL a analýza sentimentu
        rss_url = f"https://news.google.com/rss/search?q={ticker}&hl=cs&gl=CZ&ceid=CZ:cs"
        feed = feedparser.parse(rss_url)
        sentiments = []
        for entry in feed.entries:
            pol = TextBlob(entry.title).sentiment.polarity
            sentiments.append(pol)
        avg_sentiment = np.mean(sentiments) if sentiments else 0

        # Určení signálu na základě RSI a sentimentu
        signal = "SLEDOVAT"
        if last_rsi is not None:
            if last_rsi < 30 and avg_sentiment > 0:
                signal = "KOUPIT"
            elif last_rsi > 70 and avg_sentiment < 0:
                signal = "PRODAT"
            elif avg_sentiment > 0.5:
                signal = "KOUPIT"
            elif avg_sentiment < -0.5:
                signal = "PRODAT"
        else:
            if avg_sentiment > 0.5:
                signal = "KOUPIT"
            elif avg_sentiment < -0.5:
                signal = "PRODAT"

        # Výpočet počtu akcií pro daný rozpočet
        pozice = int(budget / cena) if cena and budget else 0

        vstup = round(cena, 2)
        take_profit = round(vstup * 1.10, 2)  # +10% nad vstupem
        stop_loss = round(vstup * 0.95, 2)    # -5% pod vstupem

        results.append({
            "Ticker": ticker,
            "Cena (EUR)": vstup,
            "RSI": round(last_rsi, 2) if last_rsi is not None else None,
            "Sentiment": round(avg_sentiment, 2),
            "Signál": signal,
            "Počet ks": pozice,
            "Take-Profit": take_profit,
            "Stop-Loss": stop_loss
        })

    # Zobrazení výsledků v tabulce Streamlit
    if results:
        df = pd.DataFrame(results)
        st.dataframe(df)
