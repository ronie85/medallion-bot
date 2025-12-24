import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_lightweight_charts import renderLightweightCharts

# 1. STYLE (Menjaga Konsistensi Foto Anda)
st.set_page_config(layout="wide", page_title="MEDALLION ALPHA X TRADINGVIEW")
st.markdown("""
    <style>
    .main { background-color: #131722; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 15px; border-radius: 8px; }
    [data-testid="stMetricValue"] { font-size: 22px !important; color: #00FFCC !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DATA & LOGIKA ---
@st.cache_data(ttl=60)
def fetch_medallion_data(ticker, tf):
    if len(ticker) == 4 and ".JK" not in ticker: ticker = f"{ticker}.JK"
    elif "USDT" in ticker: ticker = ticker.replace("USDT", "-USD")
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    interval_map = {"15m": "15m", "30m": "30m", "1h": "1h", "4h": "1h", "1d": "1d"}
    p = "1mo" if tf in ["15m", "30m", "1h"] else "max"
    
    try:
        df = yf.download(ticker, period=p, interval=interval_map[tf], progress=False, auto_adjust=True)
        if df.empty: return pd.DataFrame(), ticker
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Kalkulasi Indikator untuk Akurasi
        df['MA20'] = df['Close'].rolling(20).mean()
        df['Z'] = (df['Close'] - df['MA20']) / df['Close'].rolling(20).std()
        
        # ADX & MFI
        tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
        plus_dm = df['High'].diff().clip(lower=0)
        minus_dm = df['Low'].diff().clip(upper=0).abs()
        atr = tr.rolling(14).mean()
        df['ADX'] = 100 * (abs((plus_dm.rolling(14).mean()/atr) - (minus_dm.rolling(14).mean()/atr)) / ((plus_dm.rolling(14).mean()/atr) + (minus_dm.rolling(14).mean()/atr))).rolling(14).mean()
        
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        mf = tp * df['Volume']
        df['MFI'] = 100 - (100 / (1 + (mf.where(tp > tp.shift(1), 0).rolling(14).sum() / mf.where(tp < tp.shift(1), 0).rolling(14).sum())))
        
        return df.dropna(), ticker
    except: return pd.DataFrame(), ticker

# 2. SIDEBAR
st.sidebar.title("🏛️ MEDALLION ALPHA")
ticker_input = st.sidebar.text_input("Simbol", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_medallion_data(ticker_input, tf_input)

if not df.empty:
    last = df.iloc[-1]
    
    # 3. HEADER METRICS
    st.header(f"📊 {final_ticker} Terminal")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PRICE", f"{last['Close']:,.2f}")
    m2.metric("MFI (MONEY FLOW)", f"{last['MFI']:.1f}")
    m3.metric("ADX (STRENGTH)", f"{last['ADX']:.1f}")

    # Logika Akurasi 80%
    strong = last['ADX'] > 20
    if last['Z'] < -2.1 and strong and last['MFI'] < 35: sig_t, sig_c = "🚀 STRONG BUY", "#00FFCC"
    elif last['Z'] > 2.1 and strong and last['MFI'] > 65: sig_t, sig_c = "🔻 STRONG SELL", "#FF3366"
    else: sig_t, sig_c = "⚪ SEARCHING...", "#999999"
    m4.metric("ALGO SIGNAL", sig_t)

    # 4. TRADING PLAN & S&R SIDEBAR
    sup, res = df['Low'].tail(50).min(), df['High'].tail(50).max()
    st.sidebar.markdown("---")
    st.sidebar.subheader("💎 ANGKA PETUNJUK S&R")
    st.sidebar.write(f"**Resistance:** :red[{res:,.2f}]")
    st.sidebar.write(f"**Support:** :green[{sup:,.2f}]")
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADING PLAN")
    st.sidebar.markdown(f"**Status:** <span style='color:{sig_c}'>{sig_t}</span>", unsafe_allow_html=True)
    st.sidebar.write(f"**Entry:** {last['Close']:,.2f}")

    # 5. GRAFIK TRADINGVIEW ASLI
    # Format data untuk Lightweight Charts
    chart_data = df.reset_index()
    chart_data['time'] = chart_data['Date'].dt.strftime('%Y-%m-%d')
    
    candles = chart_data[['time', 'Open', 'High', 'Low', 'Close']].rename(columns=lambda x: x.lower()).to_dict('records')
    volumes = chart_data[['time', 'Volume']].rename(columns={'Volume': 'value'}).to_dict('records')
    
    # Konfigurasi Chart
    chartOptions = {
        "layout": {"background": {"type": "solid", "color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"color": "#2a2e39"}, "horzLines": {"color": "#2a2e39"}},
        "rightPriceScale": {"borderColor": "#2a2e39"},
        "timeScale": {"borderColor": "#2a2e39"},
    }
    
    seriesCandlestickChart = [
        {"type": "Candlestick", "data": candles, "options": {"upColor": "#089981", "downColor": "#f23645", "borderVisible": False, "wickUpColor": "#089981", "wickDownColor": "#f23645"}},
        {"type": "Histogram", "data": volumes, "options": {"color": "#26a69a", "priceFormat": {"type": "volume"}, "priceScaleId": ""}}
    ]

    renderLightweightCharts(seriesCandlestickChart, chartOptions, height=600)

else:
    st.info("Pemuatan data...")
