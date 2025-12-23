import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. UI SETUP
st.set_page_config(layout="wide", page_title="MEDALLION SCANNER PRO")
st.markdown("""<style>.main { background-color: #05070a; } .stMetric { border: 1px solid #1e222d; padding: 10px; }</style>""", unsafe_allow_html=True)

# 2. SCANNER ENGINE
def scan_asset(ticker, tf):
    if len(ticker) == 4 and ".JK" not in ticker: ticker = f"{ticker}.JK"
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    data = yf.download(ticker, period="1mo" if tf not in ["4h", "1d"] else "2y", interval="1h" if tf == "4h" else tf, progress=False, auto_adjust=True)
    if data.empty: return None
    if isinstance(data.columns, pd.MultiIndex): data.columns = data.columns.get_level_values(0)
    
    # Calculate Indicators
    data['MA20'] = data['Close'].rolling(20).mean()
    data['STD'] = data['Close'].rolling(20).std()
    data['Z'] = (data['Close'] - data['MA20']) / data['STD']
    data['EMA200'] = data['Close'].rolling(200).mean()
    
    last = data.iloc[-1]
    status = "NEUTRAL"
    if last['Z'] < -2.1: status = "🟢 LONG"
    elif last['Z'] > 2.1: status = "🔴 SHORT"
    
    return {"Symbol": ticker, "Price": last['Close'], "Z-Score": round(last['Z'], 2), "Trend": "BULL" if last['Close'] > last['EMA200'] else "BEAR", "Signal": status}

# 3. SIDEBAR & NAVIGATION
st.sidebar.title("🏛️ CONTROL CENTER")
mode = st.sidebar.radio("Pilih Tampilan", ["Single Asset Analysis", "Multi-Asset Scanner"])

if mode == "Multi-Asset Scanner":
    st.header("🔍 Real-Time Market Scanner")
    watchlist = ["BTC-USD", "ETH-USD", "SOL-USD", "BBCA.JK", "BMRI.JK", "GOTO.JK", "NVDA", "TSLA", "AAPL"]
    
    results = []
    with st.spinner('Scanning Market...'):
        for asset in watchlist:
            res = scan_asset(asset, "1h")
            if res: results.append(res)
    
    df_scan = pd.DataFrame(results)
    st.table(df_scan) # Tampilan tabel scanner yang bersih
    st.info("Scanner ini memantau Crypto, Saham Indo, dan Saham US secara bersamaan.")

else:
    # --- SINGLE ASSET ANALYSIS (KODE V10 SEBELUMNYA) ---
    ticker_input = st.sidebar.text_input("Asset Symbol", "BTC").upper()
    tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)
    
    # 
    
    # Ambil Data untuk Chart
    if len(ticker_input) == 4 and ".JK" not in ticker_input: ticker_final = f"{ticker_input}.JK"
    elif len(ticker_input) >= 3 and "-" not in ticker_input and ".JK" not in ticker_input: ticker_final = f"{ticker_input}-USD"
    else: ticker_final = ticker_input
    
    df = yf.download(ticker_final, period="2y" if tf_input in ["1d", "4h"] else "1mo", interval="1h" if tf_input=="4h" else tf_input, progress=False, auto_adjust=True)
    if not df.empty:
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        # Indikator Dasar
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD'] = df['Close'].rolling(20).std()
        df['Z'] = (df['Close'] - df['MA20']) / df['STD']
        df['EMA200'] = df['Close'].rolling(200).mean()
        
        last = df.iloc[-1]
        
        # Display Metrics
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Price {ticker_final}", f"{last['Close']:,.2f}")
        c2.metric("Z-Score", f"{last['Z']:.2f}")
        c3.metric("Signal", "🟢 LONG" if last['Z'] < -2.1 else "🔴 SHORT" if last['Z'] > 2.1 else "⚪ WAIT")
        
        # Charting
        fig = make_subplots(rows=1, cols=1)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='yellow', width=1), name="EMA 200"))
        fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
