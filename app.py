import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Medallion 4H Powered")

st.sidebar.header("Control Panel")
simbol = st.sidebar.text_input("Simbol Aset", "BTC-USD").upper()
# Tambahkan pilihan 4h di sini
tf_pilihan = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=3)

@st.cache_data(ttl=60)
def get_advanced_data(s, tf):
    # Jika user pilih 4h, kita ambil data 1h dulu
    fetch_tf = "1h" if tf == "4h" else tf
    d = yf.download(s, period="1mo" if tf != "1d" else "2y", interval=fetch_tf, progress=False, auto_adjust=True)
    
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    
    # PROSES RESAMPLING UNTUK 4 JAM
    if tf == "4h" and not d.empty:
        d = d.resample('4H').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
    return d

df = get_advanced_data(simbol, tf_pilihan)

if not df.empty and len(df) > 20:
    # --- STRATEGI (Z-Score & EMA) ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD']
    df['EMA200'] = df['Close'].rolling(200).mean() if len(df) > 200 else df['MA20']
    
    # Sinyal Buy
    df['Signal'] = (df['Close'] > df['EMA200']) & (df['Z_Score'] < -2.1)
    
    # --- VISUALISASI ---
    st.header(f"📊 Chart {simbol} - {tf_pilihan}")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
    
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candle"), row=1, col=1)
    
    signals = df[df['Signal']]
    if not signals.empty:
        fig.add_trace(go.Scatter(x=signals.index, y=signals['Close'], mode='markers', marker=dict(symbol='triangle-up', size=15, color='#00ff00'), name="BUY"), row=1, col=1)

    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='orange'), row=2, col=1)
    fig.update_layout(height=700, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Data tidak tersedia atau terlalu sedikit. Coba timeframe lain.")
