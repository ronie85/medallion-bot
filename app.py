import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. STYLE CONFIG (TradingView Look & Feel)
st.set_page_config(layout="wide", page_title="MEDALLION SMOOTH V21")
st.markdown("""
    <style>
    .main { background-color: #131722; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 10px; border-radius: 6px; }
    [data-testid="stMetricValue"] { font-size: 20px !important; color: #00FFCC !important; }
    /* Menghilangkan margin berlebih agar chart lebih besar */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE (Fast & Stable) ---
@st.cache_data(ttl=60)
def fetch_smooth_data(ticker, tf):
    if len(ticker) == 4 and ".JK" not in ticker: ticker = f"{ticker}.JK"
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    interval_map = {"15m": "15m", "30m": "30m", "1h": "1h", "4h": "1h", "1d": "1d"}
    p = "1mo" if tf in ["15m", "30m", "1h"] else "2y"
    
    try:
        df = yf.download(ticker, period=p, interval=interval_map[tf], progress=False, auto_adjust=True)
        if df.empty: return pd.DataFrame(), ticker
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if tf == "4h":
            df = df.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        return df.astype(float), ticker
    except:
        return pd.DataFrame(), ticker

# 2. SIDEBAR
st.sidebar.title("🏛️ MEDALLION PRO")
symbol_input = st.sidebar.text_input("Simbol (Contoh: BBCA / BTC)", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_smooth_data(symbol_input, tf_input)

if not df.empty and len(df) > 20:
    # --- INDIKATOR & S&R ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    
    # Deteksi S&R Otomatis (Area Tertinggi/Terendah 50 Candle)
    sup_val = df['Low'].tail(50).min()
    res_val = df['High'].tail(50).max()
    last = df.iloc[-1]

    # 3. METRICS BAR
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("LIVE PRICE", f"{last['Close']:,.2f}")
    c2.metric("SUPPORT", f"{sup_val:,.2f}")
    c3.metric("RESISTANCE", f"{res_val:,.2f}")
    
    # Sinyal Logic
    if last['Z'] < -2.1:
        sig, col = "🚀 LONG", "#00FFCC"
        tp, sl = last['Close']+(last['ATR']*2.5), last['Close']-(last['ATR']*1.5)
    elif last['Z'] > 2.1:
        sig, col = "🔻 SHORT", "#FF3366"
        tp, sl = last['Close']-(last['ATR']*2.5), last['Close']+(last['ATR']*1.5)
    else:
        sig, col = "⚪ WAIT", "#999999"
        tp, sl = last['Close']*1.03, last['Close']*0.98
    c4.metric("SIGNAL", sig)

    # 4. TRADING PLAN (SIDEBAR)
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 ACTION PLAN")
    st.sidebar.markdown(f"**STATUS:** <span style='color:{col}'>{sig}</span>", unsafe_allow_html=True)
    st.sidebar.write(f"**Entry:** {last['Close']:,.2f}")
    st.sidebar.success(f"**TP:** {tp:,.2f}")
    st.sidebar.error(f"**SL:** {sl:,.2f}")

    # 5. ULTRA-SMOOTH CHART (WebGL Optimized)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.85, 0.15])

    # Candlestick (Menggunakan CandlestickGL jika tersedia atau optimasi render)
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Market",
        increasing_line_color='#089981', decreasing_line_color='#f23645',
        increasing_fillcolor='#089981', decreasing_fillcolor='#f23645'
    ), row=1, col=1)

    # Automated S&R (Garis Halus Putus-putus)
    fig.add_hline(y=sup_val, line_dash="dash", line_color="#00FFCC", opacity=0.5, 
                  annotation_text="SUP", annotation_position="bottom right")
    fig.add_hline(y=res_val, line_dash="dash", line_color="#FF3366", opacity=0.5, 
                  annotation_text="RES", annotation_position="top right")

    # Volume (Background Style)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='#363a45', opacity=0.5), row=2, col=1)

    # Styling agar Mirip TradingView
    fig.update_layout(
        height=750,
        template="plotly_dark",
        paper_bgcolor='#131722',
        plot_bgcolor='#131722',
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        margin=dict(l=0, r=10, t=10, b=0),
        # Optimasi Pergerakan Halus
        dragmode='pan',
        uirevision='constant' 
    )
    
    # Skala Harga di Kanan (Standard TV)
    fig.update_yaxes(side="right", gridcolor='#2a2e39', showline=True, linecolor='#2a2e39')
    fig.update_xaxes(gridcolor='#2a2e39', showline=True, linecolor='#2a2e39')

    # Menampilkan chart dengan config interaktif tinggi
    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': True, 
        'displayModeBar': True, 
        'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
        'responsive': True
    })

else:
    st.error("Simbol tidak ditemukan. Coba ketik 'BTC' atau 'BBCA'.")
