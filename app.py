import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="Medallion Future Terminal")
st.title("📊 Medallion Alpha v8.0 (Future & Stock)")

# --- SIDEBAR CONTROL ---
st.sidebar.header("🚀 LIVE CONTROL")
asset_mode = st.sidebar.radio("Mode Aset", ["Crypto (BTCUSDT, ETHUSDT)", "Saham (BBCA, TLKM, NVDA)"])
input_user = st.sidebar.text_input("Ketik Simbol", "BTC-USD").upper()
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

# AUTO-FIXER SIMBOL (Agar pasti terbaca oleh sistem)
if asset_mode == "Crypto (BTCUSDT, ETHUSDT)":
    # Jika user ketik BTCUSDT, ubah ke BTC-USD agar yfinance bisa baca
    simbol_final = input_user.replace("USDT", "-USD")
    if "-" not in simbol_final: simbol_final = f"{input_user}-USD"
else:
    # Jika saham Indo 4 huruf, tambah .JK
    if len(input_user) == 4 and ".JK" not in input_user:
        simbol_final = f"{input_user}.JK"
    else:
        simbol_final = input_user

# 2. AMBIL DATA
@st.cache_data(ttl=30)
def get_data_stable(s, t):
    # Ambil data lebih banyak agar EMA200 tidak kosong
    p = "1mo" if t not in ["4h", "1d"] else "2y"
    i = "1h" if t == "4h" else t
    d = yf.download(s, period=p, interval=i, progress=False, auto_adjust=True)
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    if t == "4h" and not d.empty:
        d = d.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
    return d

df = get_data_stable(simbol_final, tf)

# 3. LOGIKA TRADING & DISPLAY
if not df.empty:
    # Indikator
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD']
    df['EMA200'] = df['Close'].rolling(200).mean()
    
    last_row = df.iloc[-1]
    last_price = last_row['Close']
    z_val = last_row['Z_Score']
    
    # --- PANEL SIDEBAR: ENTRY, SL, TP (WAJIB ADA) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 FUTURE TRADING PLAN")
    
    # Logika Penentuan Status
    if z_val < -2.1:
        status = "🟢 LONG (BUY)"
        color = "green"
        tp = last_price * 1.03
        sl = last_price * 0.98
    elif z_val > 2.1:
        status = "🔴 SHORT (SELL)"
        color = "red"
        tp = last_price * 0.97
        sl = last_price * 1.02
    else:
        status = "⚪ WAIT / NEUTRAL"
        color = "gray"
        tp = 0
        sl = 0

    # Menampilkan Status & Angka
    st.sidebar.markdown(f"### Status: {status}")
    st.sidebar.write(f"**Entry Price:** {last_price:,.2f}")
    if tp > 0:
        st.sidebar.success(f"**Take Profit:** {tp:,.2f}")
        st.sidebar.error(f"**Stop Loss:** {sl:,.2f}")
    st.sidebar.write(f"**Volume 24h:** {df['Volume'].iloc[-1]:,.0f}")

    # 4. METRICS HEADER
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Price", f"{last_price:,.2f}")
    c2.metric("Z-Score", f"{z_val:.2f}")
    c3.metric("EMA 200", f"{last_row['EMA200']:,.2f}")
    c4.metric("Market Trend", "BULL" if last_price > last_row['EMA200'] else "BEAR")

    # 5. GRAFIK
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
    
    # Plot Sinyal
    longs = df[df['Z_Score'] < -2.1]
    shorts = df[df['Z_Score'] > 2.1]
    fig.add_trace(go.Scatter(x=longs.index, y=longs['Close'], mode='markers', marker=dict(symbol='triangle-up', size=12, color='lime'), name="Long Signal"), row=1, col=1)
    fig.add_trace(go.Scatter(x=shorts.index, y=shorts['Close'], mode='markers', marker=dict(symbol='triangle-down', size=12, color='red'), name="Short Signal"), row=1, col=1)

    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='orange'), row=2, col=1)
    fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("Gagal memuat data. Gunakan simbol BTC-USD atau BBCA.")
