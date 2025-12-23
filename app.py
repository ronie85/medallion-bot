import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. STYLE & UI CONFIG
st.set_page_config(layout="wide", page_title="MEDALLION MASTERPIECE")
st.markdown("""
    <style>
    .main { background-color: #05070a; }
    [data-testid="stMetricValue"] { font-size: 24px; color: #00FFCC; }
    .stMetric { background: #11151c; border: 1px solid #1e222d; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DATA (STABIL & ANTI-ERROR) ---
@st.cache_data(ttl=60)
def fetch_master_data(ticker, tf):
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
    except:
        return pd.DataFrame(), ticker

# 2. SIDEBAR CONTROL
st.sidebar.title("🏛️ MEDALLION MASTER")
ticker_input = st.sidebar.text_input("Asset Symbol", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_master_data(ticker_input, tf_input)

if not df.empty and len(df) > 20:
    # --- QUANT ENGINE ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    df['EMA200'] = df['Close'].rolling(min(len(df), 200)).mean()

    last = df.iloc[-1]
    last_price = last['Close']
    z_val = last['Z']
    atr_val = last['ATR']

    # --- ACTION CENTER (STATUS LONG/SHORT SELALU TAMPIL) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 EXECUTION PLAN")
    
    # Penentuan Status
    if z_val < -2.1:
        status_trade = "🚀 LONG (BUY)"
        tp = last_price + (atr_val * 2.5)
        sl = last_price - (atr_val * 1.5)
        color_status = "lime"
    elif z_val > 2.1:
        status_trade = "🔻 SHORT (SELL)"
        tp = last_price - (atr_val * 2.5)
        sl = last_price + (atr_val * 1.5)
        color_status = "red"
    else:
        status_trade = "⚪ WAIT / NEUTRAL"
        tp = last_price * 1.03 if z_val < 0 else last_price * 0.97
        sl = last_price * 0.98 if z_val < 0 else last_price * 1.02
        color_status = "gray"

    st.sidebar.markdown(f"### Status: <span style='color:{color_status}'>{status_trade}</span>", unsafe_allow_html=True)
    st.sidebar.write(f"**Entry:** {last_price:,.2f}")
    st.sidebar.success(f"**Take Profit:** {tp:,.2f}")
    st.sidebar.error(f"**Stop Loss:** {sl:,.2f}")
    st.sidebar.info(f"**Volume:** {last['Volume']:,.0f}")

    # 3. DASHBOARD METRICS
    st.header(f"Terminal: {final_ticker}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Price", f"{last_price:,.2f}")
    m2.metric("Z-Score", f"{z_val:.2f}")
    m3.metric("ATR Volatility", f"{atr_val:.2f}")
    m4.metric("Market Trend", "BULLISH" if last_price > last['EMA200'] else "BEARISH")

    # 4. CHARTING WITH VOLUME PROFILE
    fig = make_subplots(rows=1, cols=2, column_widths=[0.8, 0.2], shared_yaxes=True, horizontal_spacing=0.01)
    
    # Main Candlestick
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='orange', width=2), name="EMA 200"), row=1, col=1)
    
    # Volume Profile (Horizontal)
    # Menghitung distribusi volume berdasarkan harga
    price_bins = pd.cut(df['Close'], bins=50)
    vpro = df.groupby(price_bins)['Volume'].sum()
    bin_centers = [b.mid for b in vpro.index]
    
    fig.add_trace(go.Bar(x=vpro.values, y=bin_centers, orientation='h', marker_color='rgba(100, 200, 255, 0.3)', name="Volume Profile"), row=1, col=2)

    fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Gunakan Simbol: BTC, ETH, BBCA, atau NVDA. Pastikan koneksi stabil.")
