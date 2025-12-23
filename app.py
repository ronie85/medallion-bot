import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. SETUP DASHBOARD
st.title("🚀 Medallion Alpha: Jim Simons Strategy")
simbol = st.sidebar.text_input("Simbol Aset", "BTC-USD")

# 2. AMBIL DATA DARI YAHOO FINANCE
df = yf.download(simbol, period="1mo", interval="15m", progress=False, auto_adjust=True)
if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

if not df.empty:
    # --- RUMUS INTI JIM SIMONS (STATISTICAL ARBITRAGE) ---
    window = 20
    # Menghitung Rata-rata Harga (Moving Average)
    df['MA20'] = df['Close'].rolling(window=window).mean()
    # Menghitung Standar Deviasi (Volatilitas)
    df['STD'] = df['Close'].rolling(window=window).std()
    # RUMUS Z-SCORE (Mencari harga yang terlalu murah/mahal secara statistik)
    df['Z_Score'] = (df['Close'] - df['MA20']) / df['STD']
    
    # --- STRATEGI PENDUKUNG (KONKRET & AKURAT) ---
    # Filter Tren Global (EMA 200)
    df['EMA200'] = df['Close'].rolling(window=200).mean()
    # Filter Volume (Ledakan Transaksi)
    df['Vol_MA'] = df['Volume'].rolling(window=20).mean()
    
    # --- LOGIKA SINYAL BELI (BUY SIGNAL) ---
    # Beli jika: Harga di atas tren besar DAN Z-Score sangat rendah DAN Volume tinggi
    df['Signal'] = (df['Close'] > df['EMA200']) & (df['Z_Score'] < -2.1) & (df['Volume'] > df['Vol_MA'] * 1.5)

    # 3. TAMPILKAN GRAFIK
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'], name="Harga", line=dict(color='black')))
    
    # Menandai Titik Entry
    signals = df[df['Signal'] == True]
    fig.add_trace(go.Scatter(x=signals.index, y=signals['Close'], mode='markers', 
                             marker=dict(symbol='triangle-up', size=15, color='lime'), name="Buy Signal"))
    
    st.plotly_chart(fig, use_container_width=True)
    st.write(f"Status Terakhir: {'🟢 SINYAL BELI' if df['Signal'].iloc[-1] else '⚪ MENUNGGU'}")
