import streamlit as st
import pandas as pd
import yfinance as yf
from binance.client import Client
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="Medallion Live Terminal")

# --- FUNGSI AMBIL DATA BINANCE (LIVE) ---
def get_binance_data(symbol, interval):
    client = Client() # Public access, no API key needed for klines
    # Mapping interval streamlit ke interval binance
    map_int = {"15m": "15m", "30m": "30m", "1h": "1h", "4h": "4h", "1d": "1d"}
    klines = client.get_historical_klines(symbol, map_int[interval], "30 days ago UTC")
    df = pd.DataFrame(klines, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTime', 'QuoteAssetVol', 'Trades', 'TakerBuyBase', 'TakerBuyQuote', 'Ignore'])
    df['Time'] = pd.to_datetime(df['Time'], unit='ms')
    df.set_index('Time', inplace=True)
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = df[col].astype(float)
    return df

# --- SIDEBAR ---
st.sidebar.header("🚀 LIVE CONTROL")
asset_type = st.sidebar.radio("Pilih Jenis Aset", ["Crypto (Binance Live)", "Saham/Lainnya (Yahoo)"])
input_user = st.sidebar.text_input("Simbol (Contoh: BTCUSDT atau BBCA)", "BTCUSDT").upper()
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

# 2. PROSES AMBIL DATA
if asset_type == "Crypto (Binance Live)":
    try:
        df = get_binance_data(input_user, tf)
    except:
        st.error("Simbol Crypto tidak valid di Binance. Contoh: BTCUSDT")
        df = pd.DataFrame()
else:
    # Logic Yahoo Finance (Auto-Fix .JK)
    simbol = f"{input_user}.JK" if len(input_user) == 4 and ".JK" not in input_user else input_user
    df = yf.download(simbol, period="2y" if tf in ["1d", "4h"] else "1mo", interval="1h" if tf=="4h" else tf, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    if tf == "4h" and not df.empty:
        df = df.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()

# 3. ANALISIS STRATEGI
if not df.empty:
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD']
    df['EMA200'] = df['Close'].rolling(200).mean()
    
    # Sinyal (Z-Score & Konfirmasi Trend)
    df['Signal'] = (df['Close'] > df['EMA200']) & (df['Z_Score'] < -2.1)

    # --- TAMPILAN DASHBOARD ---
    st.title(f"📊 Dashboard {input_user}")
    
    # Metrics Utama
    c1, c2, c3, c4 = st.columns(4)
    last_price = df['Close'].iloc[-1]
    c1.metric("Harga Terakhir", f"{last_price:,.2f}")
    c2.metric("Z-Score", f"{df['Z_Score'].iloc[-1]:.2f}")
    c3.metric("EMA 200", f"{df['EMA200'].iloc[-1]:,.2f}")
    c4.metric("Status Sinyal", "🟢 BUY" if df['Signal'].iloc[-1] else "⚪ WAIT")

    # Sidebar Info (Entry, SL, TP)
    st.sidebar.markdown("---")
    signals = df[df['Signal']]
    if not signals.empty:
        entry = signals['Close'].iloc[-1]
        st.sidebar.success(f"**ENTRY:** {entry:,.2f}")
        st.sidebar.info(f"**TP (3%):** {entry * 1.03:,.2f}")
        st.sidebar.warning(f"**SL (2%):** {entry * 0.98:,.2f}")

    # 4. GRAFIK CANDLESTICK PRO
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candle"), row=1, col=1)
    
    # Garis EMA 200
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='yellow', width=1), name="EMA 200"), row=1, col=1)

    # Sinyal Buy
    fig.add_trace(go.Scatter(x=signals.index, y=signals['Close'], mode='markers', marker=dict(symbol='triangle-up', size=15, color='#00ff00'), name="BUY"), row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='orange'), row=2, col=1)

    fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
