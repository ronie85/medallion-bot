import streamlit as st
import streamlit.components.v1 as components

# 1. UI CONFIG
st.set_page_config(layout="wide", page_title="MEDALLION X TRADINGVIEW")
st.markdown("""
    <style>
    .main { background-color: #000000; }
    .stApp { background-color: #000000; }
    </style>
    """, unsafe_allow_html=True)

# 2. SIDEBAR KONTROL
st.sidebar.title("🏛️ MEDALLION TERMINAL")
symbol = st.sidebar.text_input("Simbol Aset (Contoh: BINANCE:BTCUSDT atau IDX:BBCA)", "BINANCE:BTCUSDT").upper()
interval = st.sidebar.selectbox("Timeframe", ["1", "3", "5", "15", "30", "60", "240", "D", "W"], index=5)
theme = st.sidebar.selectbox("Tema", ["dark", "light"], index=0)

st.title(f"📊 Live Market: {symbol}")

# 3. TRADINGVIEW WIDGET ENGINE (HTML/JS)
# Kode ini memanggil library widget resmi TradingView
tradingview_widget = f"""
    <div class="tradingview-widget-container" style="height:100%;width:100%">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "autosize": true,
        "symbol": "{symbol}",
        "interval": "{interval}",
        "timezone": "Asia/Jakarta",
        "theme": "{theme}",
        "style": "1",
        "locale": "id",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "hide_top_toolbar": false,
        "hide_legend": false,
        "save_image": true,
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """

# Menampilkan Widget di Streamlit
components.html(tradingview_widget, height=700)

# 4. INFO PANEL (Optional)
st.sidebar.markdown("---")
st.sidebar.subheader("💡 Tips Simbol")
st.sidebar.info("""
- **Crypto:** BINANCE:BTCUSDT
- **Saham Indo:** IDX:BBCA
- **Saham US:** NASDAQ:NVDA
- **Forex:** FX:EURUSD
""")
