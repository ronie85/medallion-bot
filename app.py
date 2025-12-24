import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. TAMPILAN DASHBOARD (TradingView Dark Theme)
st.set_page_config(layout="wide", page_title="MEDALLION ALPHA RESTORED")
st.markdown("""
    <style>
    .main { background-color: #131722; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 15px; border-radius: 8px; }
    [data-testid="stMetricValue"] { font-size: 22px !important; color: #00FFCC !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE PEMULIHAN DATA ---
@st.cache_data(ttl=60)
def fetch_restored_data(ticker, tf):
    # Penyesuaian Simbol
    if len(ticker) == 4 and ".JK" not in ticker: ticker = f"{ticker}.JK"
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    interval_map = {"15m": "15m", "30m": "30m", "1h": "1h", "4h": "1h", "1d": "1d"}
    p = "1mo" if tf in ["15m", "30m", "1h"] else "max"
    
    try:
        df = yf.download(ticker, period=p, interval=interval_map[tf], progress=False, auto_adjust=True)
        
        if df.empty: return pd.DataFrame(), ticker

        # --- FIX: Mengatasi Kolom Bertumpuk (Multi-Index) ---
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Resample Manual untuk 4 Jam
        if tf == "4h":
            df = df.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        
        # Pastikan angka bersih
        df = df.astype(float)
        return df, ticker
    except Exception as e:
        st.error(f"Koneksi Gagal: {e}")
        return pd.DataFrame(), ticker

# 2. SIDEBAR KONTROL
st.sidebar.title("🏛️ MEDALLION PRO")
ticker_input = st.sidebar.text_input("Simbol Aset (Contoh: BTC atau BBCA)", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_restored_data(ticker_input, tf_input)

# 3. LOGIKA ANALISIS & TAMPILAN
if not df.empty and len(df) > 20:
    # Perhitungan Indikator
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    df['EMA200'] = df['Close'].rolling(min(len(df), 200)).mean()
    
    last = df.iloc[-1]
    
    # Header Metrics
    st.header(f"📊 {final_ticker} Terminal")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("HARGA LIVE", f"{last['Close']:,.2f}")
    c2.metric("Z-SCORE", f"{last['Z']:.2f}")
    c3.metric("ATR (VOL)", f"{last['ATR']:.2f}")
    
    # Penentuan Sinyal
    if last['Z'] < -2.1:
        sig_t, sig_c = "🚀 LONG / BUY", "#00FFCC"
        tp, sl = last['Close'] + (last['ATR']*2.5), last['Close'] - (last['ATR']*1.5)
    elif last['Z'] > 2.1:
        sig_t, sig_c = "🔻 SHORT / SELL", "#FF3366"
        tp, sl = last['Close'] - (last['ATR']*2.5), last['Close'] + (last['ATR']*1.5)
    else:
        sig_t, sig_c = "⚪ WAIT", "#999999"
        tp, sl = last['Close'] * 1.03, last['Close'] * 0.98

    c4.metric("STATUS", sig_t)

    # 4. TRADING PLAN (SIDEBAR)
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADING PLAN")
    st.sidebar.markdown(f"**Signal:** <span style='color:{sig_c}'>{sig_t}</span>", unsafe_allow_html=True)
    st.sidebar.write(f"**Entry:** {last['Close']:,.2f}")
    st.sidebar.success(f"**TP:** {tp:,.2f}")
    st.sidebar.error(f"**SL:** {sl:,.2f}")

    # 5. CHARTING (Visual TradingView)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.8, 0.2])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Market", increasing_line_color='#089981', decreasing_line_color='#f23645'
    ), row=1, col=1)

    # S&R Otomatis (Garis Putus-putus)
    sup = df['Low'].tail(50).min()
    res = df['High'].tail(50).max()
    fig.add_hline(y=sup, line_dash="dash", line_color="#00FFCC", opacity=0.4, annotation_text="Support", row=1, col=1)
    fig.add_hline(y=res, line_dash="dash", line_color="#FF3366", opacity=0.4, annotation_text="Resistance", row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='#363a45', name="Volume"), row=2, col=1)

    fig.update_layout(
        height=750, template="plotly_dark", paper_bgcolor='#131722', plot_bgcolor='#131722',
        xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified"
    )
    fig.update_yaxes(side="right", gridcolor='#2a2e39')
    
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("⚠️ Data belum muncul. Pastikan simbol benar (contoh: BTC atau BBCA) dan tunggu koneksi API.")
