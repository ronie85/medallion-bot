import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. UI & STYLE CONFIG
st.set_page_config(layout="wide", page_title="MEDALLION ULTIMATE V15")
st.markdown("""
    <style>
    .main { background-color: #05070a; }
    .stMetric { background: #11151c; border: 1px solid #1e222d; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI DETEKSI S&R OTOMATIS ---
def get_sr_levels(df):
    levels = []
    # Mengambil sampel data terakhir untuk deteksi fractal
    for i in range(2, len(df) - 2):
        if df['Low'][i] < df['Low'][i-1] and df['Low'][i] < df['Low'][i+1] and df['Low'][i+1] < df['Low'][i+2] and df['Low'][i-1] < df['Low'][i-2]:
            levels.append((df.index[i], df['Low'][i], 'Support'))
        if df['High'][i] > df['High'][i-1] and df['High'][i] > df['High'][i+1] and df['High'][i+1] > df['High'][i+2] and df['High'][i-1] > df['High'][i-2]:
            levels.append((df.index[i], df['High'][i], 'Resistance'))
    return levels

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def fetch_data_v15(ticker, tf):
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

# 2. SIDEBAR & INPUT
st.sidebar.title("🏛️ MEDALLION ENGINE")
ticker_input = st.sidebar.text_input("Asset Symbol", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_data_v15(ticker_input, tf_input)

if not df.empty and len(df) > 20:
    # --- QUANT CALCULATIONS ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    df['EMA200'] = df['Close'].rolling(min(len(df), 200)).mean()

    last = df.iloc[-1]
    last_price = last['Close']
    z_val = last['Z']
    atr_val = last['ATR']

    # --- SIDEBAR EXECUTION PLAN (DIJAMIN MUNCUL) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADING PLAN")
    
    if z_val < -2.1:
        status, color = "🚀 LONG", "lime"
        tp, sl = last_price + (atr_val * 2.5), last_price - (atr_val * 1.5)
    elif z_val > 2.1:
        status, color = "🔻 SHORT", "red"
        tp, sl = last_price - (atr_val * 2.5), last_price + (atr_val * 1.5)
    else:
        status, color = "⚪ NEUTRAL", "gray"
        tp, sl = last_price * 1.03, last_price * 0.98

    st.sidebar.markdown(f"### Status: <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
    st.sidebar.write(f"**Entry:** {last_price:,.2f}")
    st.sidebar.success(f"**TP:** {tp:,.2f}")
    st.sidebar.error(f"**SL:** {sl:,.2f}")

    # 3. DASHBOARD MAIN
    st.header(f"Terminal: {final_ticker}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Live Price", f"{last_price:,.2f}")
    m2.metric("Z-Score", f"{z_val:.2f}")
    m3.metric("ATR Vol", f"{atr_val:.2f}")
    m4.metric("Trend", "BULL" if last_price > last['EMA200'] else "BEAR")

    # 4. PRO CHARTING (Candle + S&R + Volume Profile)
    fig = make_subplots(rows=1, cols=2, column_widths=[0.8, 0.2], shared_yaxes=True, horizontal_spacing=0.01)
    
    # Candlestick & EMA
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='orange', width=1.5), name="EMA 200"), row=1, col=1)
    
    # --- TAMBAHKAN GARIS S&R OTOMATIS ---
    sr_levels = get_sr_levels(df.tail(150))
    for lvl in sr_levels:
        ln_color = "rgba(0, 255, 200, 0.3)" if lvl[2] == 'Support' else "rgba(255, 0, 100, 0.3)"
        fig.add_shape(type="line", x0=lvl[0], y0=lvl[1], x1=df.index[-1], y1=lvl[1], 
                      line=dict(color=ln_color, width=1, dash="dash"), row=1, col=1)

    # Volume Profile
    price_bins = pd.cut(df['Close'], bins=50)
    vpro = df.groupby(price_bins, observed=False)['Volume'].sum()
    fig.add_trace(go.Bar(x=vpro.values, y=[b.mid for b in vpro.index], orientation='h', 
                         marker_color='rgba(100, 200, 255, 0.2)', name="VPVR"), row=1, col=2)

    fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Menunggu input simbol (Contoh: BBCA atau BTC)")
