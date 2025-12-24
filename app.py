import streamlit as st
import pandas as pd
import yfinance as yf
import streamlit.components.v1 as components

# 1. SETUP UI: Memaksa Layout Full Width agar tidak sempit
st.set_page_config(layout="wide", page_title="MEDALLION ALPHA X TRADINGVIEW")

# Styling CSS untuk memastikan tidak ada padding berlebih
st.markdown("""
    <style>
    .main { background-color: #131722; }
    div[data-testid="stMetric"] { 
        background-color: #1e222d; 
        border: 1px solid #363a45; 
        padding: 10px; 
        border-radius: 8px; 
    }
    [data-testid="stMetricValue"] { font-size: 20px !important; color: #00FFCC !important; }
    /* Menghilangkan margin atas agar chart tidak terlalu jauh di bawah */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE (Untuk Sidebar & Logika) ---
@st.cache_data(ttl=60)
def fetch_data(ticker):
    yf_ticker = ticker
    if "USDT" in ticker: yf_ticker = ticker.replace("USDT", "-USD")
    elif len(ticker) == 4: yf_ticker = f"{ticker}.JK"
    
    try:
        df = yf.download(yf_ticker, period="1mo", interval="1h", progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df.astype(float)
    except: return pd.DataFrame()

# 2. SIDEBAR (Urutan Persis Foto)
st.sidebar.title("🏛️ MEDALLION ALPHA")
symbol_input = st.sidebar.text_input("Simbol", "BTCUSDT").upper()
tf_input = st.sidebar.selectbox("Timeframe Chart", ["1m", "5m", "15m", "1h", "1d"], index=3)

df = fetch_data(symbol_input)

if not df.empty:
    last_p = df['Close'].iloc[-1]
    res_l = df['High'].tail(50).max()
    sup_l = df['Low'].tail(50).min()
    
    # --- SIDEBAR: ANGKA PETUNJUK S&R ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("💎 ANGKA PETUNJUK S&R")
    st.sidebar.write(f"**Resistance:** :red[{res_l:,.2f}]")
    st.sidebar.write(f"**Support:** :green[{sup_l:,.2f}]")

    # --- SIDEBAR: TRADING PLAN ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADING PLAN")
    st.sidebar.write(f"**Entry:** {last_p:,.2f}")
    st.sidebar.success(f"**Take Profit:** {res_l:,.2f}")
    st.sidebar.error(f"**Stop Loss:** {sup_l:,.2f}")

    # 3. HEADER METRICS (Petunjuk Penting Di Atas Chart)
    # Kita pastikan 4 kolom ini muncul sebelum chart
    st.subheader(f"📊 {symbol_input} Terminal")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PRICE", f"{last_p:,.2f}")
    c2.metric("MFI (MONEY FLOW)", "32.3")
    c3.metric("ADX (STRENGTH)", "22.8")
    c4.metric("ALGO SIGNAL", "SEARCHING...")

    # 4. TRADINGVIEW CHART (Full Width 100%)
    # Menggunakan TradingView Widget asli agar petunjuk di atas chart (OHLC, Vol) muncul otomatis
    tv_symbol = symbol_input if "USDT" in symbol_input else f"IDX:{symbol_input.replace('.JK','')}"
    
    # Menyesuaikan interval untuk format TradingView
    tv_interval = "60" if tf_input == "1h" else tf_input.replace("m", "")
    
    tradingview_widget = f"""
    <div id="tv_chart_container" style="width: 100%; height: 650px;">
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
            "width": "100%",
            "height": 650,
            "symbol": "{tv_symbol}",
            "interval": "{tv_interval}",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#131722",
            "enable_publishing": false,
            "hide_side_toolbar": false,
            "allow_symbol_change": true,
            "container_id": "tv_chart_container"
        }});
        </script>
    </div>
    """
    # Menampilkan widget dengan lebar maksimal
    components.html(tradingview_widget, height=660, scrolling=False)

else:
    st.error("Data tidak ditemukan. Cek penulisan simbol.")
