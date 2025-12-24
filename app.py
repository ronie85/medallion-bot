import streamlit as st
import pandas as pd
import yfinance as yf
import streamlit.components.v1 as components

# 1. UI CONFIG (Full Dark Mode)
st.set_page_config(layout="wide", page_title="MEDALLION X TRADINGVIEW")
st.markdown("""
    <style>
    .main { background-color: #000000; }
    div[data-testid="stMetric"] { 
        background-color: #131722; 
        border: 1px solid #363a45; 
        padding: 15px; 
        border-radius: 8px; 
    }
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #00FFCC !important; }
    iframe { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- QUANT ENGINE (Mencari Angka Petunjuk S&R) ---
def get_sr_data(symbol):
    # Penyesuaian simbol untuk perhitungan internal
    yf_symbol = symbol.split(':')[-1]
    if "BTC" in yf_symbol and "-" not in yf_symbol: yf_symbol = "BTC-USD"
    if len(yf_symbol) == 4: yf_symbol = f"{yf_symbol}.JK"
    
    try:
        df = yf.download(yf_symbol, period="1mo", interval="1h", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # Matematika S&R & Sinyal
        support_price = df['Low'].tail(50).min()
        resistance_price = df['High'].tail(50).max()
        
        df['MA20'] = df['Close'].rolling(20).mean()
        df['STD'] = df['Close'].rolling(20).std()
        z_score = (df['Close'].iloc[-1] - df['MA20'].iloc[-1]) / df['STD'].iloc[-1]
        atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        
        return {
            "price": df['Close'].iloc[-1],
            "sup": support_price,
            "res": resistance_price,
            "z": z_score,
            "atr": atr
        }
    except:
        return None

# 2. SIDEBAR CONTROL
st.sidebar.title("🏛️ MEDALLION ALPHA")
symbol_input = st.sidebar.text_input("Simbol (Contoh: BINANCE:BTCUSDT atau IDX:BBCA)", "BINANCE:BTCUSDT").upper()
tf_input = st.sidebar.selectbox("Timeframe Chart", ["1", "5", "15", "60", "240", "D"], index=3)

# Jalankan Kalkulasi Angka Petunjuk
sr_data = get_sr_data(symbol_input)

if sr_data:
    # --- PANEL PETUNJUK ANGKA S&R ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("💎 ANGKA PETUNJUK S&R")
    st.sidebar.markdown(f"**Resistance:** <span style='color:#FF3366'>{sr_data['res']:,.2f}</span>", unsafe_allow_html=True)
    st.sidebar.markdown(f"**Support:** <span style='color:#00FFCC'>{sr_data['sup']:,.2f}</span>", unsafe_allow_html=True)
    
    # Logic Sinyal
    if sr_data['z'] < -2.1:
        status, color = "🚀 LONG", "#00FFCC"
        tp, sl = sr_data['price'] + (sr_data['atr']*2.5), sr_data['price'] - (sr_data['atr']*1.5)
    elif sr_data['z'] > 2.1:
        status, color = "🔻 SHORT", "#FF3366"
        tp, sl = sr_data['price'] - (sr_data['atr']*2.5), sr_data['price'] + (sr_data['atr']*1.5)
    else:
        status, color = "⚪ NEUTRAL", "#999999"
        tp, sl = sr_data['price'] * 1.03, sr_data['price'] * 0.98

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADING PLAN")
    st.sidebar.markdown(f"**Status:** <span style='color:{color}'>{status}</span>", unsafe_allow_html=True)
    st.sidebar.write(f"**Entry:** {sr_data['price']:,.2f}")
    st.sidebar.success(f"**TP:** {tp:,.2f}")
    st.sidebar.error(f"**SL:** {sl:,.2f}")

# 3. MAIN DASHBOARD (TRADINGVIEW WIDGET)
st.title(f"📊 Live Terminal: {symbol_input}")

# Metrik Utama di Atas Chart
if sr_data:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current Price", f"{sr_data['price']:,.2f}")
    m2.metric("Guide Resistance", f"{sr_data['res']:,.0f}")
    m3.metric("Guide Support", f"{sr_data['sup']:,.0f}")
    m4.metric("Market Vol (ATR)", f"{sr_data['atr']:.2f}")

# Widget TradingView Ukuran Besar
tv_widget = f"""
    <div style="height: 750px;">
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
          "autosize": true,
          "symbol": "{symbol_input}",
          "interval": "{tf_input}",
          "timezone": "Asia/Jakarta",
          "theme": "dark",
          "style": "1",
          "locale": "id",
          "toolbar_bg": "#f1f3f6",
          "enable_publishing": false,
          "allow_symbol_change": true,
          "container_id": "tv_chart_container"
        }});
        </script>
        <div id="tv_chart_container" style="height: 750px;"></div>
    </div>
"""
components.html(tv_widget, height=760)
