import streamlit as st
import pandas as pd
import yfinance as yf
import streamlit.components.v1 as components

# 1. STYLE DASHBOARD (Dark Theme & Blue Background)
st.set_page_config(layout="wide", page_title="MEDALLION ALPHA X TRADINGVIEW")
st.markdown("""
    <style>
    .main { background-color: #131722; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 15px; border-radius: 8px; }
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #00FFCC !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE (Untuk Perhitungan Sidebar) ---
@st.cache_data(ttl=60)
def fetch_data(ticker):
    # Penyesuaian Simbol untuk Yahoo Finance
    yf_ticker = ticker
    if "USDT" in ticker: yf_ticker = ticker.replace("USDT", "-USD")
    elif len(ticker) == 4: yf_ticker = f"{ticker}.JK"
    
    try:
        df = yf.download(yf_ticker, period="1mo", interval="1h", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df.astype(float)
    except: return pd.DataFrame()

# 2. SIDEBAR (Urutan Persis Foto: Simbol -> Timeframe -> S&R -> Plan)
st.sidebar.title("🏛️ MEDALLION ALPHA")
# Default BTCUSDT seperti di foto
symbol_input = st.sidebar.text_input("Simbol", "BTCUSDT").upper()
tf_input = st.sidebar.selectbox("Timeframe Chart", ["1m", "30m", "1h", "1d"], index=2)

df = fetch_data(symbol_input)

if not df.empty:
    # Logika Angka Petunjuk (Hanya Angka, Tidak di Gambar)
    last_price = df['Close'].iloc[-1]
    res_level = df['High'].tail(50).max()
    sup_level = df['Low'].tail(50).min()
    atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
    
    # --- BAGIAN SIDEBAR: ANGKA PETUNJUK S&R ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("💎 ANGKA PETUNJUK S&R")
    st.sidebar.write(f"**Resistance:** :red[{res_level:,.2f}]")
    st.sidebar.write(f"**Support:** :green[{sup_level:,.2f}]")

    # --- BAGIAN SIDEBAR: TRADING PLAN (HANYA TEKS) ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADING PLAN")
    # Logika Sederhana untuk Status
    status = "SEARCHING..."
    if last_price < sup_level * 1.01: status = "BUY SIGNAL"
    elif last_price > res_level * 0.99: status = "SELL SIGNAL"
    
    st.sidebar.write(f"**Status:** {status}")
    st.sidebar.write(f"**Entry:** {last_price:,.2f}")
    st.sidebar.success(f"**Take Profit:** {last_price + (atr*2):,.2f}")
    st.sidebar.error(f"**Stop Loss:** {last_price - (atr*1.5):,.2f}")

    # 3. HEADER METRICS (4 Kotak Atas)
    st.header(f"📊 {symbol_input} Terminal")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PRICE", f"{last_price:,.2f}")
    c2.metric("MFI (MONEY FLOW)", "32.3") # Contoh angka statis sesuai foto
    c3.metric("ADX (STRENGTH)", "22.8")   # Contoh angka statis sesuai foto
    c4.metric("ALGO SIGNAL", status)

    # 4. CHART TRADINGVIEW (Widget Asli Tanpa Garis Tambahan)
    # Ini akan memunculkan chart interaktif TradingView asli di tengah
    tv_symbol = symbol_input if "USDT" in symbol_input else f"IDX:{symbol_input.replace('.JK','')}"
    
    tradingview_widget = f"""
    <div class="tradingview-widget-container" style="height:600px;">
        <div id="tradingview_chart"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
            "autosize": true,
            "symbol": "{tv_symbol}",
            "interval": "{tf_input.replace('m','') if 'm' in tf_input else '60'}",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "hide_top_toolbar": false,
            "save_image": false,
            "container_id": "tradingview_chart"
        }});
        </script>
    </div>
    """
    components.html(tradingview_widget, height=650)
else:
    st.warning("Menunggu data...")
