import streamlit as st
import pandas as pd
import yfinance as yf
import streamlit.components.v1 as components

# 1. SETTING LAYOUT (FULL WIDTH)
st.set_page_config(layout="wide", page_title="MEDALLION HYBRID PRO")
st.markdown("""
    <style>
    .main { background-color: #000000; }
    iframe { border-radius: 10px; border: 1px solid #363a45; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 15px; border-radius: 10px; }
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #00FFCC !important; }
    </style>
    """, unsafe_allow_html=True)

# --- QUANT ENGINE (UNTUK DATA PENDUKUNG) ---
def get_quant_signals(ticker):
    # Penyesuaian simbol khusus untuk yfinance (internal calculation)
    yf_ticker = ticker.split(':')[-1]
    if "BTC" in yf_ticker and "-" not in yf_ticker: yf_ticker = "BTC-USD"
    if len(yf_ticker) == 4: yf_ticker = f"{yf_ticker}.JK"
    
    try:
        df = yf.download(yf_ticker, period="1mo", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Perhitungan Matematika
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD'] = df['Close'].rolling(20).std()
        df['Z'] = (df['Close'] - df['MA20']) / df['STD']
        df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
        
        last = df.iloc[-1]
        return last
    except:
        return None

# 2. SIDEBAR CONTROL
st.sidebar.title("🏛️ MEDALLION ALPHA")
symbol_input = st.sidebar.text_input("Asset (Contoh: BINANCE:BTCUSDT atau IDX:BBCA)", "BINANCE:BTCUSDT").upper()
timeframe = st.sidebar.selectbox("Timeframe Chart", ["1", "5", "15", "60", "240", "D"], index=3)

# Jalankan Kalkulasi Sinyal
stats = get_quant_signals(symbol_input)

if stats is not None:
    # --- DATA PENDUKUNG (ENTRY, SL, TP) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADING STRATEGY")
    
    price = stats['Close']
    z_score = stats['Z']
    atr = stats['ATR']
    
    if z_score < -2.1:
        status, color = "🚀 LONG / BUY", "#00FFCC"
        tp, sl = price + (atr * 2.5), price - (atr * 1.5)
    elif z_score > 2.1:
        status, color = "🔻 SHORT / SELL", "#FF3366"
        tp, sl = price - (atr * 2.5), price + (atr * 1.5)
    else:
        status, color = "⚪ NEUTRAL", "#999999"
        tp, sl = price * 1.03, price * 0.98

    st.sidebar.markdown(f"### Status: <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
    st.sidebar.metric("Live Price", f"{price:,.2f}")
    st.sidebar.success(f"**Target Profit:** {tp:,.2f}")
    st.sidebar.error(f"**Stop Loss:** {sl:,.2f}")
    st.sidebar.info(f"**Volatility (ATR):** {atr:.2f}")

# 3. MAIN DASHBOARD (TRADINGVIEW BESAR)
st.title(f"📊 Terminal TradingView: {symbol_input}")

# Kode Widget dengan Ukuran Maksimal
tv_widget = f"""
    <div style="height: 800px;">
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
          "autosize": true,
          "symbol": "{symbol_input}",
          "interval": "{timeframe}",
          "timezone": "Asia/Jakarta",
          "theme": "dark",
          "style": "1",
          "locale": "id",
          "toolbar_bg": "#f1f3f6",
          "enable_publishing": false,
          "withdateranges": true,
          "hide_side_toolbar": false,
          "allow_symbol_change": true,
          "container_id": "tv_chart_container"
        }});
        </script>
        <div id="tv_chart_container" style="height: 800px;"></div>
    </div>
"""

# Menampilkan Chart TV berukuran besar
components.html(tv_widget, height=820)

# 4. BOTTOM METRICS
if stats is not None:
    m1, m2, m3 = st.columns(3)
    m1.metric("Current Z-Score", f"{z_score:.2f}")
    m2.metric("ATR Volatility", f"{atr:.2f}")
    m3.metric("Market Signal", status)
