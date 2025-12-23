import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. UI PRO SETUP
st.set_page_config(layout="wide", page_title="MEDALLION QUANT V12")
st.markdown("""<style>.main { background-color: #05070a; } .stMetric { border-radius: 10px; background: #11151c; border: 1px solid #1e222d; }</style>""", unsafe_allow_html=True)

# --- FUNGSI DETEKSI S&R OTOMATIS ---
def get_sr_levels(df):
    levels = []
    for i in range(2, df.shape[0] - 2):
        # Deteksi Fractal (Low & High)
        if df['Low'][i] < df['Low'][i-1] and df['Low'][i] < df['Low'][i+1] and df['Low'][i+1] < df['Low'][i+2] and df['Low'][i-1] < df['Low'][i-2]:
            levels.append((df.index[i], df['Low'][i], 'Support'))
        if df['High'][i] > df['High'][i-1] and df['High'][i] > df['High'][i+1] and df['High'][i+1] > df['High'][i+2] and df['High'][i-1] > df['High'][i-2]:
            levels.append((df.index[i], df['High'][i], 'Resistance'))
    return levels

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def get_data_v12(ticker, tf):
    if len(ticker) == 4 and ".JK" not in ticker: ticker = f"{ticker}.JK"
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    p = "1mo" if tf not in ["4h", "1d"] else "2y"
    i = "1h" if tf == "4h" else tf
    d = yf.download(ticker, period=p, interval=i, progress=False, auto_adjust=True)
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    
    if tf == "4h" and not d.empty:
        d = d.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
    return d, ticker

# 2. SIDEBAR
st.sidebar.title("🏛️ QUANT V12 ENGINE")
ticker_input = st.sidebar.text_input("Asset Symbol", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)
show_sr = st.sidebar.checkbox("Tampilkan S&R Otomatis", value=True)

df, final_ticker = get_data_v12(ticker_input, tf_input)

if not df.empty:
    # 3. RUMUS LANJUTAN (Z-SCORE + ATR + VOLATILITY)
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    df['EMA200'] = df['Close'].rolling(200).mean()

    # 4. DASHBOARD HEADER
    last = df.iloc[-1]
    atr = last['ATR']
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Live Price", f"{last['Close']:,.2f}")
    c2.metric("Z-Score", f"{last['Z']:.2f}")
    c3.metric("ATR Volatility", f"{atr:.2f}")
    c4.metric("EMA 200", f"{last['EMA200']:,.2f}")

    # 5. CHARTING DENGAN S&R
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.8, 0.2])
    
    # Candlestick
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market"), row=1, col=1)
    
    # EMA 200
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='orange', width=1.5), name="EMA 200"), row=1, col=1)

    # SINYAL LONG/SHORT
    longs = df[df['Z'] < -2.2]
    shorts = df[df['Z'] > 2.2]
    fig.add_trace(go.Scatter(x=longs.index, y=longs['Close'], mode='markers', marker=dict(symbol='triangle-up', size=12, color='lime'), name="Long Signal"), row=1, col=1)
    fig.add_trace(go.Scatter(x=shorts.index, y=shorts['Close'], mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name="Short Signal"), row=1, col=1)

    # --- S&R LOGIC ---
    if show_sr:
        sr_levels = get_sr_levels(df.tail(200)) # Ambil level dari 200 candle terakhir
        for lvl in sr_levels:
            color = "rgba(0, 255, 200, 0.4)" if lvl[2] == 'Support' else "rgba(255, 0, 100, 0.4)"
            fig.add_shape(type="line", x0=lvl[0], y0=lvl[1], x1=df.index[-1], y1=lvl[1], 
                          line=dict(color=color, width=1, dash="dash"), row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='#1f77b4', name="Volume"), row=2, col=1)

    fig.update_layout(height=850, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # ACTION PLAN SIDEBAR
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 EXECUTION PLAN")
    if last['Z'] < -2.2:
        st.sidebar.success(f"**SIGNAL: LONG**\n\nTP: {last['Close']+(atr*2.5):,.2f}\n\nSL: {last['Close']-(atr*1.5):,.2f}")
    elif last['Z'] > 2.2:
        st.sidebar.error(f"**SIGNAL: SHORT**\n\nTP: {last['Close']-(atr*2.5):,.2f}\n\nSL: {last['Close']+(atr*1.5):,.2f}")
    else:
        st.sidebar.info("Wait for Extreme Signal")

else:
    st.error("Invalid Symbol. Gunakan BTC, BBCA, atau NVDA.")
