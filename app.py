import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="Medallion Future & Stock")
st.title("📊 Medallion Alpha v7.0 (Future & Stock)")

# --- FUNGSI AMBIL DATA BINANCE (TANPA LIBRARY KHUSUS) ---
def get_binance_live(symbol, interval):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=500"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTime', 'QuoteAssetVol', 'Trades', 'TakerBuyBase', 'TakerBuyQuote', 'Ignore'])
    df['Time'] = pd.to_datetime(df['Time'], unit='ms')
    df.set_index('Time', inplace=True)
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = df[col].astype(float)
    return df

# --- SIDEBAR CONTROL ---
st.sidebar.header("🚀 LIVE CONTROL")
asset_mode = st.sidebar.radio("Mode Aset", ["Crypto (Binance Future)", "Saham (Yahoo Finance)"])
input_user = st.sidebar.text_input("Simbol (Contoh: BTCUSDT / BBCA)", "BTCUSDT").upper()
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

# 2. EKSEKUSI AMBIL DATA
if asset_mode == "Crypto (Binance Future)":
    try:
        df = get_binance_live(input_user, tf)
    except:
        st.error("Gagal mengambil data Binance. Pastikan simbol benar (contoh: BTCUSDT).")
        df = pd.DataFrame()
else:
    # Logic Saham (Auto-Fix .JK)
    simbol_yf = f"{input_user}.JK" if len(input_user) == 4 and ".JK" not in input_user else input_user
    df = yf.download(simbol_yf, period="2y" if tf in ["1d", "4h"] else "1mo", interval="1h" if tf=="4h" else tf, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    if tf == "4h" and not df.empty:
        df = df.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()

# 3. ANALISIS STRATEGI (LONG & SHORT)
if not df.empty:
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD']
    df['EMA200'] = df['Close'].rolling(200).mean()
    
    # LOGIKA SINYAL (Agar tetap muncul di TF Kecil)
    # Jika Z-Score di bawah -2.1 = Potensi LONG (Beli murah)
    # Jika Z-Score di atas 2.1 = Potensi SHORT (Jual mahal)
    df['Signal_Long'] = (df['Z_Score'] < -2.1)
    df['Signal_Short'] = (df['Z_Score'] > 2.1)

    # --- TAMPILAN DASHBOARD ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Trading Signal Status")
    
    last_row = df.iloc[-1]
    last_price = last_row['Close']
    
    if last_row['Z_Score'] < -2.1:
        st.sidebar.success("🚀 STATUS: LONG (BUY)")
        entry_price = last_price
        st.sidebar.write(f"**Entry:** {entry_price:,.2f}")
        st.sidebar.write(f"**Take Profit (3%):** {entry_price * 1.03:,.2f}")
        st.sidebar.write(f"**Stop Loss (2%):** {entry_price * 0.98:,.2f}")
    elif last_row['Z_Score'] > 2.1:
        st.sidebar.error("🔻 STATUS: SHORT (SELL)")
        entry_price = last_price
        st.sidebar.write(f"**Entry:** {entry_price:,.2f}")
        st.sidebar.write(f"**Take Profit (3%):** {entry_price * 0.97:,.2f}")
        st.sidebar.write(f"**Stop Loss (2%):** {entry_price * 1.02:,.2f}")
    else:
        st.sidebar.info("⌛ STATUS: WAIT / NEUTRAL")

    # 4. METRICS HEADER
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Harga Live", f"{last_price:,.2f}")
    c2.metric("Z-Score", f"{last_row['Z_Score']:.2f}")
    c3.metric("EMA 200", f"{last_row['EMA200']:,.2f}")
    c4.metric("Market", "BULLISH" if last_price > last_row['EMA200'] else "BEARISH")

    # 5. GRAFIK CANDLESTICK
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candle"), row=1, col=1)
    
    # Plot Sinyal di Grafik
    long_signals = df[df['Signal_Long']]
    short_signals = df[df['Signal_Short']]
    
    fig.add_trace(go.Scatter(x=long_signals.index, y=long_signals['Close'], mode='markers', marker=dict(symbol='triangle-up', size=12, color='lime'), name="LONG"), row=1, col=1)
    fig.add_trace(go.Scatter(x=short_signals.index, y=short_signals['Close'], mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name="SHORT"), row=1, col=1)

    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='orange'), row=2, col=1)
    fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Data tidak ditemukan. Masukkan simbol yang benar.")
