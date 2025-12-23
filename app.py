import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Medallion Backtester")

# --- SIDEBAR ---
st.sidebar.header("Konfigurasi Uji Coba")
simbol = st.sidebar.text_input("Simbol Aset", "BBCA.JK").upper()
tf = st.sidebar.selectbox("Timeframe", ["1d", "1h", "30m", "15m"], index=0)
st.sidebar.markdown("---")

# --- AMBIL DATA ---
@st.cache_data(ttl=60)
def get_data(s, t):
    d = yf.download(s, period="1y", interval=t, progress=False, auto_adjust=True)
    if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
    return d

df = get_data(simbol, tf)

if not df.empty and len(df) > 200:
    # 1. KALKULASI STRATEGI
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD']
    df['EMA200'] = df['Close'].rolling(200).mean()
    
    # Sinyal Entry
    df['Signal'] = (df['Close'] > df['EMA200']) & (df['Z_Score'] < -2.1)
    
    # 2. MESIN BACKTEST (Simulasi Seperti Colab)
    df['Returns'] = df['Close'].pct_change()
    # Asumsi: Kita Take Profit 3% atau Stop Loss 2%
    tp = 0.03 
    sl = -0.02
    
    trades = []
    for i in range(len(df)):
        if df['Signal'].iloc[i]:
            entry_price = df['Close'].iloc[i]
            # Cari hasil di masa depan (maksimal 10 bar kedepan)
            for j in range(i+1, min(i+11, len(df))):
                ret = (df['Close'].iloc[j] - entry_price) / entry_price
                if ret >= tp or ret <= sl:
                    trades.append(ret)
                    break

    # 3. STATISTIK HASIL UJI
    win_rate = (len([t for t in trades if t > 0]) / len(trades) * 100) if trades else 0
    total_profit = sum(trades) * 100 if trades else 0

    # TAMPILKAN HASIL UJI (Seperti Output Colab)
    st.header(f"📈 Hasil Backtest: {simbol}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Sinyal Muncul", f"{len(trades)} Kali")
    c2.metric("Win Rate", f"{win_rate:.2f}%")
    c3.metric("Total Profit Estimasi", f"{total_profit:.2f}%")

    # 4. GRAFIK CANDLESTICK
    fig = make_subplots(rows=1, cols=1)
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
    
    # Tandai sinyal yang muncul
    signals = df[df['Signal']]
    fig.add_trace(go.Scatter(x=signals.index, y=signals['Close'], mode='markers', 
                             marker=dict(symbol='triangle-up', size=12, color='lime'), name="Entry Signal"))
    
    fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Data tidak cukup untuk melakukan backtest (Butuh minimal 200 bar data).")
