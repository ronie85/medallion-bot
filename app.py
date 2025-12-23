import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# CONFIGURASI UI BERKELAS
st.set_page_config(layout="wide", page_title="QUANT TERMINAL PRO")
st.markdown("""
    <style>
    .main { background-color: #0E1117; }
    div[data-testid="stMetricValue"] { font-size: 22px; color: #00FFCC; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Medallion Quant Terminal")

# SIDEBAR PRO
st.sidebar.title("STRETEGY ENGINE")
asset_mode = st.sidebar.selectbox("Market Mode", ["Crypto Future", "Stock Market"])
input_user = st.sidebar.text_input("Asset Symbol", "BTC-USD").upper()
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

# ANALYTIC PARAMETERS
z_threshold = st.sidebar.slider("Z-Score Threshold", 1.5, 3.0, 2.2)

# FETCH DATA
@st.cache_data(ttl=30)
def get_pro_data(s, t):
    p = "1mo" if t not in ["4h", "1d"] else "2y"
    i = "1h" if t == "4h" else t
    d = yf.download(s, period=p, interval=i, progress=False, auto_adjust=True)
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    if t == "4h" and not d.empty:
        d = d.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
    return d

df = get_pro_data(input_user, tf)

if not df.empty:
    # --- QUANTITATIVE ENGINE ---
    # 1. Z-Score (Mean Reversion)
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD']
    
    # 2. ATR (Volatility Based Stop Loss)
    high_low = df['High'] - df['Low']
    df['ATR'] = high_low.rolling(14).mean()
    
    # 3. EMA 200 (Trend Filter)
    df['EMA200'] = df['Close'].rolling(200).mean()

    # LOGIK SIGNAL
    last_row = df.iloc[-1]
    last_price = last_row['Close']
    atr_val = last_row['ATR']
    
    # SIDEBAR ACTION CENTER
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ EXECUTION PLAN")
    
    if last_row['Z_Score'] < -z_threshold:
        st.sidebar.success("🚀 POSITION: LONG")
        tp = last_price + (atr_val * 2) # TP berdasarkan volatilitas
        sl = last_price - (atr_val * 1.5)
        st.sidebar.write(f"**Entry:** {last_price:,.2f}")
        st.sidebar.write(f"**TP (ATR 2.0):** {tp:,.2f}")
        st.sidebar.write(f"**SL (ATR 1.5):** {sl:,.2f}")
    elif last_row['Z_Score'] > z_threshold:
        st.sidebar.error("🔻 POSITION: SHORT")
        tp = last_price - (atr_val * 2)
        sl = last_price + (atr_val * 1.5)
        st.sidebar.write(f"**Entry:** {last_price:,.2f}")
        st.sidebar.write(f"**TP (ATR 2.0):** {tp:,.2f}")
        st.sidebar.write(f"**SL (ATR 1.5):** {sl:,.2f}")
    else:
        st.sidebar.info("Neutral - No Signal")

    # MAIN DASHBOARD METRICS
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Price", f"{last_price:,.2f}")
    m2.metric("Z-Score", f"{last_row['Z_Score']:.2f}")
    m3.metric("ATR (Volatility)", f"{atr_val:.4f}")
    m4.metric("Trend State", "BULLISH" if last_price > last_row['EMA200'] else "BEARISH")

    # PRO CHARTING
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.8, 0.2])
    
    # Candlestick
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market"), row=1, col=1)
    
    # EMA 200 Line
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='#FFD700', width=1.5), name="EMA 200"), row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='#1f77b4', name="Volume"), row=2, col=1)

    fig.update_layout(height=850, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Invalid Symbol or Data Timeout.")
