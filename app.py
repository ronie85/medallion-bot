import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. KONFIGURASI HALAMAN
st.set_page_config(layout="wide", page_title="Medallion Ultimate Terminal")
st.title("📊 Medallion Alpha: Pro Dashboard")

# --- SIDEBAR CONTROL ---
st.sidebar.header("Control Panel")
simbol_input = st.sidebar.text_input("Simbol (Contoh: BBCA, BTC, NVDA)", "ETH-USD").upper()

# Auto-Fixer Simbol (Mengenali saham Indo, US, atau Crypto)
if ".JK" not in simbol_input and "-" not in simbol_input and len(simbol_input) == 4:
    simbol = f"{simbol_input}.JK"
elif "-" not in simbol_input and len(simbol_input) <= 4 and ".JK" not in simbol_input:
    simbol = f"{simbol_input}-USD"
else:
    simbol = simbol_input

tf_pilihan = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=3)

# 2. FUNGSI AMBIL DATA (Dengan Fitur Resampling 4 Jam)
@st.cache_data(ttl=60)
def get_advanced_data(s, tf):
    fetch_tf = "1h" if tf == "4h" else tf
    # Ambil periode lebih panjang untuk EMA200
    period = "2y" if tf in ["1d", "4h"] else "1mo"
    
    try:
        d = yf.download(s, period=period, interval=fetch_tf, progress=False, auto_adjust=True)
        if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
        
        if tf == "4h" and not d.empty:
            d = d.resample('4H').agg({
                'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
            }).dropna()
        return d
    except:
        return pd.DataFrame()

df = get_advanced_data(simbol, tf_pilihan)

if not df.empty and len(df) > 20:
    # --- KALKULASI STRATEGI JIM SIMONS ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD']
    df['EMA200'] = df['Close'].rolling(200).mean()
    
    # Logika Sinyal (Hanya Buy jika di atas EMA200 & Z-Score anjlok)
    if len(df) > 200:
        df['Signal'] = (df['Close'] > df['EMA200']) & (df['Z_Score'] < -2.1)
    else:
        df['Signal'] = (df['Z_Score'] < -2.1)

    # --- PANEL ANGKA DI SIDEBAR ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("📍 Detail Harga Terakhir")
    
    signals = df[df['Signal'] == True]
    if not signals.empty:
        last_entry = signals['Close'].iloc[-1]
        tp_level = last_entry * 1.03  # Target Profit 3%
        sl_level = last_entry * 0.98  # Stop Loss 2%
        
        st.sidebar.success(f"**Entry:** ${last_entry:,.2f}")
        st.sidebar.info(f"**Take Profit:** ${tp_level:,.2f}")
        st.sidebar.warning(f"**Stop Loss:** ${sl_level:,.2f}")
        st.sidebar.write(f"**Volume:** {df['Volume'].iloc[-1]:,.0f}")
    else:
        st.sidebar.write("Menunggu Sinyal Baru...")

    # 3. TAMPILAN METRICS UTAMA (HEADER)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Harga Market", f"${df['Close'].iloc[-1]:,.2f}")
    c2.metric("Z-Score", f"{df['Z_Score'].iloc[-1]:.2f}")
    c3.metric("Volume", f"{df['Volume'].iloc[-1]:,.0f}")
    c4.metric("Status Sinyal", "🟢 BUY" if df['Signal'].iloc[-1] else "⚪ WAIT")

    # 4. GRAFIK CANDLESTICK & VOLUME
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    
    # Panel Candlestick
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Harga"), row=1, col=1)
    
    # Tandai Titik Beli
    if not signals.empty:
        fig.add_trace(go.Scatter(x=signals.index, y=signals['Close'], mode='markers', 
                                 marker=dict(symbol='triangle-up', size=15, color='#00ff00'), name="BUY SIGNAL"), row=1, col=1)

    # Panel Volume
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='orange'), row=2, col=1)
    
    fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # 5. TABEL RIWAYAT
    st.write("### 📜 Riwayat Sinyal 10 Terakhir")
    st.dataframe(signals.tail(10), use_container_width=True)
else:
    st.error("Data tidak ditemukan. Tips: Gunakan format 'BBCA' untuk saham Indo atau 'BTC' untuk crypto.")
