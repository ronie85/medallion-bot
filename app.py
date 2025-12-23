import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. UI CONFIG (TRADINGVIEW DARK STYLE)
st.set_page_config(layout="wide", page_title="MEDALLION PRO TERMINAL")
st.markdown("""
    <style>
    .main { background-color: #131722; }
    [data-testid="stMetricValue"] { font-size: 22px; color: #00FFCC; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DATA ---
@st.cache_data(ttl=60)
def fetch_final_data(ticker, tf):
    # Auto-Fixer
    if len(ticker) == 4 and ".JK" not in ticker: ticker = f"{ticker}.JK"
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    interval_map = {"15m": "15m", "30m": "30m", "1h": "1h", "4h": "1h", "1d": "1d"}
    p = "1mo" if tf in ["15m", "30m", "1h"] else "max"
    
    try:
        df = yf.download(ticker, period=p, interval=interval_map[tf], progress=False, auto_adjust=True)
        if df.empty: return pd.DataFrame(), ticker
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if tf == "4h":
            df = df.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        return df, ticker
    except:
        return pd.DataFrame(), ticker

# 2. SIDEBAR
st.sidebar.title("🏛️ TERMINAL ENGINE")
ticker_input = st.sidebar.text_input("Asset Symbol", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_final_data(ticker_input, tf_input)

if not df.empty and len(df) > 20:
    # --- CALCULATIONS ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    df['EMA200'] = df['Close'].rolling(min(len(df), 200)).mean()
    
    last = df.iloc[-1]
    
    # 3. HEADER METRICS
    st.title(f"📊 {final_ticker} Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PRICE", f"{last['Close']:,.2f}")
    c2.metric("Z-SCORE", f"{last['Z']:.2f}")
    c3.metric("ATR (VOLATILITY)", f"{last['ATR']:.2f}")
    
    # Logic Signal & Trading Plan (SIDEBAR)
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 EXECUTION PLAN")
    
    if last['Z'] < -2.1:
        sig_text, sig_col = "🚀 LONG", "#00FFCC"
        tp, sl = last['Close'] + (last['ATR']*2.5), last['Close'] - (last['ATR']*1.5)
    elif last['Z'] > 2.1:
        sig_text, sig_col = "🔻 SHORT", "#FF3366"
        tp, sl = last['Close'] - (last['ATR']*2.5), last['Close'] + (last['ATR']*1.5)
    else:
        sig_text, sig_col = "⚪ NEUTRAL", "#999999"
        tp, sl = last['Close'] * 1.03, last['Close'] * 0.98

    c4.metric("SIGNAL", sig_text
