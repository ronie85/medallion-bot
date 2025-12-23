import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. UI SETUP
st.set_page_config(layout="wide", page_title="MEDALLION SNIPER V13")
st.markdown("""<style>.main { background-color: #05070a; } .stMetric { border-radius: 10px; background: #11151c; border: 1px solid #1e222d; }</style>""", unsafe_allow_html=True)

# --- FUNGSI ANALISIS DATA ---
def analyze_data(df):
    if df.empty or len(df) < 50: return df
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    df['EMA200'] = df['Close'].rolling(200).mean()
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    return df

# --- DATA FETCHING ENGINE ---
@st.cache_data(ttl=60)
def get_mtf_data(ticker, main_tf):
    if len(ticker) == 4 and ".JK" not in ticker: ticker = f"{ticker}.JK"
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    # Ambil Data Utama (Current TF)
    p = "1mo" if main_tf not in ["4h", "1d"] else "2y"
    i = "1h" if main_tf == "4h" else main_tf
    df_main = yf.download(ticker, period=p, interval=i, progress=False, auto_adjust=True)
    if isinstance(df_main.columns, pd.MultiIndex): df_main.columns = df_main.columns.get_level_values(0)
    if main_tf == "4h": df_main = df_main.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
    
    # Ambil Data Validasi (Higher TF)
    higher_tf = "1d" if main_tf in ["1h", "4h"] else "1wk" if main_tf == "1d" else "4h"
    df_higher = yf.download(ticker, period="2y", interval="1d" if higher_tf == "1d" else "1h", progress=False, auto_adjust=True)
    if isinstance(df_higher.columns, pd.MultiIndex): df_higher.columns = df_higher.columns.get_level_values(0)
    if higher_tf == "4h": df_higher = df_higher.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
    
    return analyze_data(df_main), analyze_data(df_higher), ticker

# 2. SIDEBAR
st.sidebar.title("🏛️ SNIPER ENGINE V13")
ticker_input = st.sidebar.text_input("Asset Symbol", "BTC").upper()
main_tf = st.sidebar.selectbox("Main Timeframe (Entry)", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, df_htf, final_ticker = get_mtf_data(ticker_input, main_tf)

if not df.empty and not df_htf.empty:
    last_main = df.iloc[-1]
    last_htf = df_htf.iloc[-1]
    
    # 3. LOGIKA SNIPER (VALIDASI MTF)
    # LONG: Z-Score Rendah di Main TF DAN Harga di atas EMA200 di Higher TF
    is_long = (last_main['Z'] < -2.1) and (last_main['Close'] > last_htf['EMA200'])
    # SHORT: Z-Score Tinggi di Main TF DAN Harga di bawah EMA200 di Higher TF
    is_short = (last_main['Z'] > 2.1) and (last_main
