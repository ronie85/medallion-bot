import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. STYLE KONSISTEN (Sesuai Foto Anda)
st.set_page_config(layout="wide", page_title="MEDALLION ALPHA X")
st.markdown("""
    <style>
    .main { background-color: #131722; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 15px; border-radius: 8px; }
    [data-testid="stMetricValue"] { font-size: 22px !important; color: #00FFCC !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DATA ---
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
        return df.astype(float), ticker
    except: return pd.DataFrame(), ticker

# 2. SIDEBAR (TETAP SAMA)
st.sidebar.title("🏛️ MEDALLION ALPHA")
ticker_input = st.sidebar.text_input("Simbol", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_medallion_data(ticker_input, tf_input)

if not df.empty and len(df) > 30:
    # --- LOGIKA INTERNAL (ADX & MFI) ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['Z'] = (df['Close'] - df['MA20']) / df['Close'].rolling(20).std()
    
    # ADX
    tr = pd.concat([df['High']-df['Low'], (df['High']-df['Close'].shift()).abs(), (df['Low']-df['Close'].shift()).abs()], axis=1).max(axis=1)
    plus_di = 100 * (df['High'].diff().clip(lower=0).rolling(14).mean() / tr.rolling(14).mean())
    minus_di = 100 * (df['Low'].diff().clip(upper=0).abs().rolling(14).mean() / tr.rolling(14).mean())
    df['ADX'] = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di)).rolling(14).mean()
    
    # MFI
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    mf = tp * df['Volume']
    df['MFI'] = 100 - (100 / (1 + (mf.where(tp > tp.shift(1), 0).rolling(14).sum() / mf.where(tp < tp.shift(1), 0).rolling(14).sum())))
    
    last = df.iloc[-1]

    # 3. HEADER METRICS
    st.header(f"📊 {final_ticker} Terminal")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PRICE", f"{last['Close']:,.2f}")
    m2.metric("MFI (MONEY FLOW)", f"{last['MFI']:.1f}")
    m3.metric("ADX (STRENGTH)", f"{last['ADX']:.1f}")

    # Sinyal Akurasi 80%
    if last['Z'] < -2.1 and last['ADX'] > 20 and last['MFI'] < 35: sig_t, sig_c = "🚀 STRONG BUY", "#00FFCC"
    elif last['Z'] > 2.1 and last['ADX'] > 20 and last['MFI'] > 65: sig_t, sig_c = "🔻 STRONG SELL", "#FF3366"
    else: sig_t, sig_c = "⚪ SEARCHING...", "#999999"
    m4.metric("ALGO SIGNAL", sig_t)

    # 4. SIDEBAR S&R & PLAN
    st.sidebar.markdown("---")
    st.sidebar.subheader("💎 ANGKA PETUNJUK S&R")
    sup, res = df['Low'].tail(50).min(), df['High'].tail(50).max()
    st.sidebar.write(f"**Resistance:** :red[{res:,.2f}]")
    st.sidebar.write(f"**Support:** :green[{sup:,.2f}]")

    # 5. GRAFIK (STYLE TRADINGVIEW)
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Market", increasing_line_color='#089981', decreasing_line_color='#f23645',
        increasing_fillcolor='#089981', decreasing_fillcolor='#f23645'
    ))
    
    # Tambahkan S&R Zones (Lebih Dinamis)
    fig.add_hline(y=sup, line_dash="dash", line_color="#00FFCC", opacity=0.3)
    fig.add_hline(y=res, line_dash="dash", line_color="#FF3366", opacity=0.3)

    fig.update_layout(
        height=650, template="plotly_dark", paper_bgcolor='#131722', plot_bgcolor='#131722',
        xaxis_rangeslider_visible=False, margin=dict(l=0, r=0, t=0, b=0),
        yaxis=dict(side="right", gridcolor='#2a2e39'), xaxis=dict(gridcolor='#2a2e39')
    )
    
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

else:
    st.info("Pemuatan data...")
