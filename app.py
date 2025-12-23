import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="Medallion Quant Terminal")
st.title("📊 Medallion Alpha: Pro Dashboard")

# SIDEBAR CONTROL
st.sidebar.header("Control Panel")
simbol = st.sidebar.text_input("Simbol Aset", "ETH-USD")
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "1d"], index=2)

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

    # 3. HEADER METRICS (Harga & Info)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Harga Terakhir", f"${df['Close'].iloc[-1]:,.2f}")
    c2.metric("Z-Score", f"{df['Z_Score'].iloc[-1]:.2f}")
    c3.metric("Volume", f"{df['Volume'].iloc[-1]:,.0f}")
    c4.metric("Status Sinyal", "🟢 BUY" if df['Signal'].iloc[-1] else "⚪ WAIT")

    # 4. GRAFIK INTERAKTIF (2 PANEL: HARGA & VOLUME)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

    # Panel Atas: Candlestick/Line + SL + TP
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Price", line=dict(color='white')), row=1, col=1)
    
    # Menandai Entry, TP, dan SL untuk sinyal terakhir
    signals = df[df['Signal'] == True]
    if not signals.empty:
        last_entry = signals['Close'].iloc[-1]
        tp_level = last_entry * 1.02  # Take Profit 2%
        sl_level = last_entry * 0.98  # Stop Loss 2%
        
        # Plot Segitiga Buy
        fig.add_trace(go.Scatter(x=signals.index, y=signals['Close'], mode='markers', 
                                 marker=dict(symbol='triangle-up', size=15, color='#00ff00'), name="Entry Point"), row=1, col=1)
        
        # Garis TP & SL (Hanya muncul jika ada sinyal aktif)
        fig.add_trace(go.Scatter(x=[signals.index[-1], df.index[-1]], y=[tp_level, tp_level], 
                                 line=dict(color='cyan', dash='dot'), name="Take Profit (2%)"), row=1, col=1)
        fig.add_trace(go.Scatter(x=[signals.index[-1], df.index[-1]], y=[sl_level, sl_level], 
                                 line=dict(color='red', dash='dot'), name="Stop Loss (2%)"), row=1, col=1)

    # Panel Bawah: Volume
    colors = ['red' if v > m * 1.5 else 'gray' for v, m in zip(df['Volume'], df['Vol_MA'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color=colors), row=2, col=1)

    fig.update_layout(height=700, template="plotly_dark", showlegend=True, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # 5. TABEL HASIL TRADE
    st.write("### 📜 Riwayat Sinyal & Detail Harga Entry")
    summary = signals[['Close', 'Volume', 'Z_Score']].copy()
    summary.columns = ['Harga Entry', 'Volume Transaksi', 'Z-Score']
    st.dataframe(summary.tail(10), use_container_width=True)

else:
    st.error("Data tidak ditemukan. Pastikan simbol benar (contoh: BTC-USD).")
