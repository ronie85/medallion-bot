import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from streamlit_lightweight_charts import renderLightweightCharts

# 1. UI CONFIG
st.set_page_config(layout="wide", page_title="MEDALLION QUANT PRO")
st.markdown("""
    <style>
    .main { background-color: #131722; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 15px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DATA & S&R ---
@st.cache_data(ttl=60)
def get_pro_data(ticker, tf):
    if len(ticker) == 4: ticker = f"{ticker}.JK"
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    df = yf.download(ticker, period="1y", interval="1h" if tf == "4h" else tf, progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    if tf == "4h":
        df = df.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
    return df, ticker

# 2. SIDEBAR
st.sidebar.title("🏛️ QUANT TERMINAL")
symbol_input = st.sidebar.text_input("Asset Symbol", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["1h", "4h", "1d"], index=0)

df, final_ticker = get_pro_data(symbol_input, tf_input)

if not df.empty:
    # --- QUANT CALCULATIONS ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    
    last = df.iloc[-1]
    
    # Deteksi S&R Otomatis (Fractal)
    sup_val = df['Low'].tail(50).min()
    res_val = df['High'].tail(50).max()

    # --- TRADING PLAN SIDEBAR ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADING PLAN")
    
    if last['Z'] < -2.1:
        status, col = "🚀 LONG", "#00FFCC"
        tp, sl = last['Close']+(last['ATR']*2.5), last['Close']-(last['ATR']*1.5)
    elif last['Z'] > 2.1:
        status, col = "🔻 SHORT", "#FF3366"
        tp, sl = last['Close']-(last['ATR']*2.5), last['Close']+(last['ATR']*1.5)
    else:
        status, col = "⚪ NEUTRAL", "#999999"
        tp, sl = last['Close']*1.03, last['Close']*0.97

    st.sidebar.markdown(f"### Status: <span style='color:{col}'>{status}</span>", unsafe_allow_html=True)
    st.sidebar.write(f"**Entry:** {last['Close']:,.2f}")
    st.sidebar.success(f"**Target Profit:** {tp:,.2f}")
    st.sidebar.error(f"**Stop Loss:** {sl:,.2f}")

    # --- FORMAT DATA UNTUK LIGHTWEIGHT CHARTS ---
    chart_data = df.reset_index()
    chart_data.columns = ['time', 'open', 'high', 'low', 'close', 'volume'] + list(chart_data.columns[6:])
    # Convert time to timestamp
    chart_data['time'] = chart_data['time'].apply(lambda x: x.timestamp())

    # 3. MAIN DISPLAY
    st.title(f"📈 {final_ticker} Professional Chart")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Live Price", f"{last['Close']:,.2f}")
    m2.metric("Support (Auto)", f"{sup_val:,.2f}")
    m3.metric("Resistance (Auto)", f"{res_val:,.2f}")

    # Konfigurasi Chart TradingView Style
    chartOptions = {
        "layout": {"background": {"type": "solid", "color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"color": "#2a2e39"}, "horzLines": {"color": "#2a2e39"}},
        "crosshair": {"mode": 0},
        "priceScale": {"borderColor": "#485c7b"},
        "timeScale": {"borderColor": "#485c7b", "timeVisible": True, "secondsVisible": False},
    }

    renderLightweightCharts([
        {
            "type": "Candlestick",
            "data": chart_data[['time', 'open', 'high', 'low', 'close']].to_dict('records'),
            "options": {
                "upColor": "#089981", "downColor": "#f23645", 
                "borderVisible": False, "wickUpColor": "#089981", "wickDownColor": "#f23645"
            },
            "markers": [
                {"time": chart_data['time'].iloc[-1], "position": "belowBar", "color": "#00FFCC", "shape": "arrowUp", "text": "SUP"} if last['Close'] <= sup_val * 1.01 else {},
            ]
        }
    ], chartOptions)

    # Menampilkan S&R sebagai teks bantuan karena limitasi library rendering sederhana
    st.info(f"💡 **Analisis S&R Otomatis:** Harga saat ini tertahan di antara Support **{sup_val:,.2f}** dan Resistance **{res_val:,.2f}**.")

else:
    st.error("Gagal memuat data. Periksa simbol aset Anda.")
