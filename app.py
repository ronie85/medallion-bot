import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. SETUP UI
st.set_page_config(layout="wide", page_title="MEDALLION STABLE V14")
st.title("🛡️ Medallion Quant: Anti-Error Edition")

# --- DATA ENGINE DENGAN PROTEKSI ---
@st.cache_data(ttl=60)
def fetch_safe_data(ticker, tf):
    # Auto-fix Simbol
    if len(ticker) == 4 and ".JK" not in ticker: ticker = f"{ticker}.JK"
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    # Penyesuaian Interval
    interval_map = {"15m": "15m", "30m": "30m", "1h": "1h", "4h": "1h", "1d": "1d"}
    p = "1mo" if tf in ["15m", "30m", "1h"] else "2y"
    
    try:
        df = yf.download(ticker, period=p, interval=interval_map[tf], progress=False, auto_adjust=True)
        if df.empty: return pd.DataFrame(), ticker
        
        # Flatten Columns jika MultiIndex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Resample Manual untuk 4 Jam
        if tf == "4h":
            df = df.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        return df, ticker
    except Exception as e:
        st.error(f"Error Fetching Data: {e}")
        return pd.DataFrame(), ticker

# 2. SIDEBAR
st.sidebar.header("⚙️ CONFIGURATION")
ticker_input = st.sidebar.text_input("Symbol (BBCA / BTC)", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_safe_data(ticker_input, tf_input)

# 3. ANALISIS & VISUALISASI
if not df.empty and len(df) > 20:
    try:
        # Kalkulasi Indikator
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD'] = df['Close'].rolling(20).std()
        df['Z'] = (df['Close'] - df['MA20']) / df['STD']
        df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
        
        # EMA200 (Gunakan MA biasa jika data < 200 untuk hindari error)
        if len(df) >= 200:
            df['EMA200'] = df['Close'].rolling(200).mean()
        else:
            df['EMA200'] = df['Close'].rolling(len(df)).mean()

        last = df.iloc[-1]
        
        # Metrics Dashboard
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Price", f"{last['Close']:,.2f}")
        c2.metric("Z-Score", f"{last['Z']:.2f}")
        c3.metric("ATR", f"{last['ATR']:.2f}")
        status = "🟢 LONG" if last['Z'] < -2.1 else "🔴 SHORT" if last['Z'] > 2.1 else "⚪ NEUTRAL"
        c4.metric("Status", status)

        # Plotting
        fig = make_subplots(rows=1, cols=1)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Market"))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='orange', width=1.5), name="Trend Line"))
        
        fig.update_layout(height=600, template="plotly_dark", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # Sniper Execution Plan
        st.sidebar.markdown("---")
        if last['Z'] < -2.1:
            st.sidebar.success(f"**BUY SIGNAL**\n\nTP: {last['Close']+(last['ATR']*2.5):,.2f}\n\nSL: {last['Close']-(last['ATR']*1.5):,.2f}")
        elif last['Z'] > 2.1:
            st.sidebar.error(f"**SELL SIGNAL**\n\nTP: {last['Close']-(last['ATR']*2.5):,.2f}\n\nSL: {last['Close']+(last['ATR']*1.5):,.2f}")

    except Exception as e:
        st.error(f"Kalkulasi Strategi Error: {e}")
else:
    st.warning("Menunggu data... Pastikan simbol benar dan koneksi internet stabil.")
