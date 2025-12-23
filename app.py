import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="Medallion Quant Terminal")
st.title("📊 Medallion Alpha: Pro Dashboard")

# --- SIDEBAR CONTROL ---
st.sidebar.header("Control Panel")
simbol = st.sidebar.text_input("Simbol Aset", "ETH-USD")
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "1d"], index=0)

# 2. FUNGSI AMBIL DATA
@st.cache_data(ttl=60)
def get_pro_data(s, t):
    d = yf.download(s, period="1mo", interval=t, progress=False, auto_adjust=True)
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    return d

df = get_pro_data(simbol, tf)

if not df.empty:
    # --- KALKULASI STRATEGI ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD']
    df['EMA200'] = df['Close'].rolling(200).mean()
    df['Vol_MA'] = df['Volume'].rolling(20).mean()
    
    # Sinyal Buy (Jim Simons Hybrid)
    df['Signal'] = (df['Close'] > df['EMA200']) & (df['Z_Score'] < -2.1) & (df['Volume'] > df['Vol_MA'] * 1.5)
    
    # --- LOGIKA ANGKA DI SIDEBAR ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📍 Detail Harga Terakhir")
    
    signals = df[df['Signal'] == True]
    if not signals.empty:
        last_entry = signals['Close'].iloc[-1]
        tp_level = last_entry * 1.02  # Take Profit 2%
        sl_level = last_entry * 0.98  # Stop Loss 2%
        last_vol = df['Volume'].iloc[-1]
        
        # Menampilkan Angka di bawah Timeframe
        st.sidebar.success(f"**Entry:** ${last_entry:,.2f}")
        st.sidebar.info(f"**Take Profit:** ${tp_level:,.2f}")
        st.sidebar.warning(f"**Stop Loss:** ${sl_level:,.2f}")
        st.sidebar.write(f"**Volume:** {last_vol:,.0f}")
    else:
        st.sidebar.write("Menunggu Sinyal...")

    # 3. HEADER METRICS UTAMA
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Harga Market", f"${df['Close'].iloc[-1]:,.2f}")
    c2.metric("Z-Score", f"{df['Z_Score'].iloc[-1]:.2f}")
    c3.metric("Volume", f"{df['Volume'].iloc[-1]:,.0f}")
    c4.metric("Status", "🟢 BUY" if df['Signal'].iloc[-1] else "⚪ WAIT")

    # 4. GRAFIK CANDLESTICK
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

    # PANEL 1: CANDLESTICK
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="Candlestick"
    ), row=1, col=1)
    
    # Menandai Entry Point
    if not signals.empty:
        fig.add_trace(go.Scatter(
            x=signals.index, y=signals['Close'], 
            mode='markers', 
            marker=dict(symbol='triangle-up', size=15, color='#00ff00'), 
            name="Entry Point"
        ), row=1, col=1)

    # PANEL 2: VOLUME
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'], 
        name="Volume", 
        marker_color='orange'
    ), row=2, col=1)

    fig.update_layout(
        height=800, 
        template="plotly_dark", 
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.write("### 📜 Riwayat Sinyal")
    st.dataframe(signals.tail(10), use_container_width=True)
else:
    st.error("Gagal memuat data. Periksa simbol aset.")
