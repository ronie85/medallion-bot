import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. SETUP UI (TradingView Dark Theme)
st.set_page_config(layout="wide", page_title="MEDALLION ALPHA PRO")
st.markdown("""
    <style>
    .main { background-color: #131722; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 10px; border-radius: 5px; }
    [data-testid="stMetricValue"] { font-size: 20px !important; color: #00FFCC !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DATA ---
@st.cache_data(ttl=60)
def fetch_safe_data(ticker, tf):
    # Auto-Fixer Simbol
    if len(ticker) == 4 and ".JK" not in ticker: ticker = f"{ticker}.JK"
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    interval_map = {"15m": "15m", "30m": "30m", "1h": "1h", "4h": "1h", "1d": "1d"}
    p = "1mo" if tf in ["15m", "30m", "1h"] else "max"
    
    try:
        df = yf.download(ticker, period=p, interval=interval_map[tf], progress=False, auto_adjust=True)
        if df.empty: return pd.DataFrame(), ticker
        
        # Bersihkan MultiIndex jika ada
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Resample Manual untuk 4 Jam
        if tf == "4h":
            df = df.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        
        # Pastikan tipe data float
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = df[col].astype(float)
            
        return df, ticker
    except:
        return pd.DataFrame(), ticker

# 2. SIDEBAR
st.sidebar.title("🏛️ MEDALLION PRO")
ticker_input = st.sidebar.text_input("Asset Symbol", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_safe_data(ticker_input, tf_input)

if not df.empty and len(df) > 20:
    # --- QUANTITATIVE ENGINE ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    df['EMA200'] = df['Close'].rolling(min(len(df), 200)).mean()
    
    last = df.iloc[-1]
    
    # 3. HEADER METRICS
    st.header(f"📊 {final_ticker} Terminal")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PRICE", f"{last['Close']:,.2f}")
    c2.metric("Z-SCORE", f"{last['Z']:.2f}")
    c3.metric("ATR (VOL)", f"{last['ATR']:.2f}")
    
    # Logic Signal
    if last['Z'] < -2.1:
        sig_text, sig_col = "🚀 LONG", "#00FFCC"
        tp, sl = last['Close'] + (last['ATR']*2.5), last['Close'] - (last['ATR']*1.5)
    elif last['Z'] > 2.1:
        sig_text, sig_col = "🔻 SHORT", "#FF3366"
        tp, sl = last['Close'] - (last['ATR']*2.5), last['Close'] + (last['ATR']*1.5)
    else:
        sig_text, sig_col = "⚪ NEUTRAL", "#999999"
        tp, sl = last['Close'] * 1.03, last['Close'] * 0.98

    c4.metric("SIGNAL", sig_text)

    # 4. SIDEBAR TRADING PLAN
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADING PLAN")
    st.sidebar.markdown(f"**Status:** <span style='color:{sig_col}'>{sig_text}</span>", unsafe_allow_html=True)
    st.sidebar.write(f"**Entry:** {last['Close']:,.2f}")
