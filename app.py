import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. SETTING UI (DARK THEME TRADINGVIEW)
st.set_page_config(layout="wide", page_title="TRADINGVIEW CLONE PRO")
st.markdown("""
    <style>
    .main { background-color: #131722; }
    .stApp { background-color: #131722; }
    [data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 10px; border-radius: 4px; }
    [data-testid="stMetricValue"] { color: #00FFCC !important; font-size: 20px !important; }
    .block-container { padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def fetch_tv_data(ticker, tf):
    if len(ticker) == 4 and ".JK" not in ticker: ticker = f"{ticker}.JK"
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    interval_map = {"15m": "15m", "30m": "30m", "1h": "1h", "4h": "1h", "1d": "1d"}
    p = "1mo" if tf in ["15m", "30m", "1h"] else "2y"
    
    try:
        df = yf.download(ticker, period=p, interval=interval_map[tf], progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if tf == "4h":
            df = df.resample('4H').agg({'Open':'first','High':'max','Low':'min','Close':'last','Volume':'sum'}).dropna()
        return df.astype(float), ticker
    except:
        return pd.DataFrame(), ticker

# 2. SIDEBAR
st.sidebar.title("🏛️ TERMINAL SETTINGS")
symbol = st.sidebar.text_input("Asset (BTC / BBCA)", "BTC").upper()
tf = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_tv_data(symbol, tf)

if not df.empty and len(df) > 20:
    # --- MATH ENGINE ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    
    last = df.iloc[-1]
    sup = df['Low'].tail(50).min()
    res = df['High'].tail(50).max()

    # 3. TOP METRICS
    st.subheader(f"📊 {final_ticker}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PRICE", f"{last['Close']:,.2f}")
    c2.metric("S&R ZONE", f"{sup:,.0f} - {res:,.0f}")
    
    # Signal Logic
    if last['Z'] < -2.1:
        sig, col = "🚀 LONG", "#00FFCC"
        tp, sl = last['Close']+(last['ATR']*2.5), last['Close']-(last['ATR']*1.5)
    elif last['Z'] > 2.1:
        sig, col = "🔻 SHORT", "#FF3366"
        tp, sl = last['Close']-(last['ATR']*2.5), last['Close']+(last['ATR']*1.5)
    else:
        sig, col = "⚪ WAIT", "#999999"
        tp, sl = last['Close']*1.03, last['Close']*0.98
    
    c3.metric("ATR VOL", f"{last['ATR']:.2f}")
    c4.metric("SIGNAL", sig)

    # 4. CHART (TRADINGVIEW CORE)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.01, row_heights=[0.85, 0.15])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Price", increasing_line_color='#089981', decreasing_line_color='#f23645',
        increasing_fillcolor='#089981', decreasing_fillcolor='#f23645'
    ), row=1, col=1)

    # Automated S&R (Clean Lines)
    fig.add_hline(y=sup, line_dash="dash", line_color="#00FFCC", opacity=0.4, 
                  annotation_text="SUPPORT", annotation_position="bottom right")
    fig.add_hline(y=res, line_dash="dash", line_color="#FF3366", opacity=0.4, 
                  annotation_text="RESISTANCE", annotation_position="top right")

    # Volume (Background)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='#26a69a', opacity=0.3), row=2, col=1)

    # Layout Customization (THE SECRET TO TV LOOK)
    fig.update_layout(
        height=800,
        template="plotly_dark",
        paper_bgcolor='#131722',
        plot_bgcolor='#131722',
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        margin=dict(l=0, r=50, t=0, b=0),
        dragmode='pan', # Memungkinkan geser grafik seperti TV
        spikedistance=-1, # Crosshair line
    )

    # Right Side Axis
    fig.update_yaxes(side="right", gridcolor='#2a2e39', zeroline=False, showspikes=True, spikemode='across', spikethickness=1, spikedash='solid', spikecolor='#606060')
    fig.update_xaxes(gridcolor='#2a2e39', zeroline=False, showspikes=True, spikemode='across', spikethickness=1, spikedash='solid', spikecolor='#606060')

    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': False})

    # 5. SIDEBAR TRADING PLAN
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 ACTION PLAN")
    st.sidebar.markdown(f"**Status:** <span style='color:{col}'>{sig}</span>", unsafe_allow_html=True)
    st.sidebar.write(f"**Entry:** {last['Close']:,.2f}")
    st.sidebar.success(f"**TP:** {tp:,.2f}")
    st.sidebar.error(f"**SL:** {sl:,.2f}")

else:
    st.error("Gagal memuat data. Periksa simbol.")
