import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. SETUP TAMPILAN (Sesuai Foto: Dark Blue Theme)
st.set_page_config(layout="wide", page_title="MEDALLION ALPHA X TRADINGVIEW")
st.markdown("""
    <style>
    .main { background-color: #131722; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 15px; border-radius: 8px; }
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #00FFCC !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def fetch_data(ticker, tf):
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

# 2. SIDEBAR (Urutan Persis Seperti Foto Anda)
st.sidebar.title("🏛️ MEDALLION ALPHA")
ticker_input = st.sidebar.text_input("Simbol", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe Chart", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_data(ticker_input, tf_input)

if not df.empty and len(df) > 30:
    # --- LOGIKA INTERNAL ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['Z'] = (df['Close'] - df['MA20']) / df['Close'].rolling(20).std()
    
    # Perbaikan: Hitung pct_change pada seluruh kolom sebelum mengambil baris terakhir
    df['Pct_Change'] = df['Close'].pct_change()
    
    last = df.iloc[-1]
    
    # 3. HEADER METRICS (4 Kotak di Atas)
    st.header(f"📊 {final_ticker} Terminal")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PRICE", f"{last['Close']:,.2f}")
    
    # Sinyal Berbasis Z-Score
    if last['Z'] < -2.1: sig_t, sig_c = "🚀 BUY", "#00FFCC"
    elif last['Z'] > 2.1: sig_t, sig_c = "🔻 SELL", "#FF3366"
    else: sig_t, sig_c = "⚪ NEUTRAL", "#999999"
    
    # Menampilkan Volatilitas (Perubahan Harga Terakhir)
    m2.metric("CHANGE", f"{last['Pct_Change']:.2%}")
    m3.metric("Z-SCORE", f"{last['Z']:.2f}")
    m4.metric("SIGNAL", sig_t)

    # 4. SIDEBAR ANGKA PETUNJUK & PLAN (Sesuai Foto)
    st.sidebar.markdown("---")
    st.sidebar.subheader("💎 ANGKA PETUNJUK S&R")
    sup, res = df['Low'].tail(50).min(), df['High'].tail(50).max()
    st.sidebar.write(f"**Resistance:** :red[{res:,.2f}]")
    st.sidebar.write(f"**Support:** :green[{sup:,.2f}]")

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADING PLAN")
    st.sidebar.markdown(f"**Status:** <span style='color:{sig_c}'>{sig_t}</span>", unsafe_allow_html=True)
    st.sidebar.write(f"**Entry:** {last['Close']:,.2f}")

    # 5. CHART (Gaya Klasik Foto Anda)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.8, 0.2])
    
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Market", increasing_line_color='#089981', decreasing_line_color='#f23645'
    ), row=1, col=1)
    
    fig.add_hline(y=sup, line_dash="dash", line_color="#00FFCC", opacity=0.4, row=1, col=1)
    fig.add_hline(y=res, line_dash="dash", line_color="#FF3366", opacity=0.4, row=1, col=1)

    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='#363a45', name="Volume"), row=2, col=1)

    fig.update_layout(
        height=700, template="plotly_dark", paper_bgcolor='#131722', plot_bgcolor='#131722',
        xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10)
    )
    fig.update_yaxes(side="right", gridcolor='#2a2e39')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Input simbol dan tunggu pemuatan data...")
