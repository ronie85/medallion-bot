import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. UI TRADINGVIEW DARK THEME
st.set_page_config(layout="wide", page_title="MEDALLION TERMINAL PRO")
st.markdown("""
    <style>
    .main { background-color: #131722; } /* Warna Dasar TradingView */
    [data-testid="stSidebar"] { background-color: #1e222d; border-right: 1px solid #363a45; }
    .stMetric { background: #1e222d; border: 1px solid #363a45; padding: 10px; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DATA & S&R ---
@st.cache_data(ttl=60)
def fetch_tv_data(ticker, tf):
    if len(ticker) == 4 and ".JK" not in ticker: ticker = f"{ticker}.JK"
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    interval_map = {"15m": "15m", "30m": "30m", "1h": "1h", "4h": "1h", "1d": "1d"}
    p = "1mo" if tf in ["15m", "30m", "1h"] else "max"
    
    try:
        df = yf.download(ticker, period=p, interval=interval_map[tf], progress=False, auto_adjust=True)
        if df.empty: return pd.DataFrame(), ticker
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if tf == "4h":
            df = df.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        return df, ticker
    except: return pd.DataFrame(), ticker

# 2. SIDEBAR CONFIG
st.sidebar.title("🛠️ CHART SETTINGS")
ticker_input = st.sidebar.text_input("Asset Symbol", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)
show_volume = st.sidebar.toggle("Show Volume Overlay", value=True)

df, final_ticker = fetch_tv_data(ticker_input, tf_input)

if not df.empty and len(df) > 20:
    # --- INDICATORS ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    df['EMA200'] = df['Close'].rolling(min(len(df), 200)).mean()
    
    last = df.iloc[-1]
    
    # 3. TOP METRICS BAR
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PRICE", f"{last['Close']:,.2f}")
    c2.metric("CHANGE", f"{( (last['Close']-df['Open'].iloc[-1]) / df['Open'].iloc[-1] * 100):.2f}%")
    c3.metric("ATR", f"{last['ATR']:.2f}")
    c4.metric("VOL", f"{last['Volume']:,.0f}")

    # 4. DYNAMIC CHART (TRADINGVIEW STYLE)
    # Create subplot: 1 main chart with a hidden volume axis
    fig = make_subplots(rows=1, cols=1, specs=[[{"secondary_y": True}]])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Market", increasing_line_color='#089981', decreasing_line_color='#f23645',
        increasing_fillcolor='#089981', decreasing_fillcolor='#f23645'
    ), secondary_y=True)

    # EMA 200 (Smoothing)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='#ff9800', width=1.5), name="EMA 200"), secondary_y=True)

    # S&R ZONES (Dynamic Area)
    # Detect recent peaks for Support/Resistance
    recent_df = df.tail(100)
    sup = recent_df['Low'].min()
    res = recent_df['High'].max()
    
    # Add Support Zone
    fig.add_hrect(y0=sup * 0.998, y1=sup * 1.002, fillcolor="green", opacity=0.1, line_width=0, secondary_y=True)
    # Add Resistance Zone
    fig.add_hrect(y0=res * 0.998, y1=res * 1.002, fillcolor="red", opacity=0.1, line_width=0, secondary_y=True)

    # Volume Overlay (Like TradingView)
    if show_volume:
        fig.add_trace(go.Bar(
            x=df.index, y=df['Volume'], name="Volume", 
            marker_color='rgba(128, 128, 128, 0.2)', yaxis="y"
        ), secondary_y=False)

    # 5. EXECUTION PLAN ON SIDEBAR
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADE SIGNAL")
    if last['Z'] < -2.1:
        st.sidebar.success(f"**SIGNAL: BUY**\n\nTP: {last['Close']+(last['ATR']*2.5):,.2f}\
