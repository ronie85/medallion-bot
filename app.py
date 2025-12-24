import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. STYLE CONFIG (TradingView Look)
st.set_page_config(layout="wide", page_title="MEDALLION TITAN V20")
st.markdown("""
    <style>
    .main { background-color: #131722; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 15px; border-radius: 10px; }
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #00FFCC !important; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def fetch_stable_data(ticker, tf):
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
st.sidebar.title("🏛️ MEDALLION TITAN")
symbol_input = st.sidebar.text_input("Asset Symbol", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_stable_data(symbol_input, tf_input)

if not df.empty and len(df) > 20:
    # --- INDICATORS ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
    df['EMA200'] = df['Close'].rolling(min(len(df), 200)).mean()
    
    # S&R LOGIC (Automated)
    support = df['Low'].tail(50).min()
    resistance = df['High'].tail(50).max()
    last = df.iloc[-1]

    # 3. METRICS HEADER
    st.header(f"📊 {final_ticker} Professional Dashboard")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PRICE", f"{last['Close']:,.2f}")
    m2.metric("S&R ZONE", f"{support:,.0f} - {resistance:,.0f}")
    m3.metric("ATR VOL", f"{last['ATR']:.2f}")

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
    m4.metric("SIGNAL", sig)

    # 4. SIDEBAR TRADING PLAN
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADING PLAN")
    st.sidebar.markdown(f"**Status:** <span style='color:{col}'>{sig}</span>", unsafe_allow_html=True)
    st.sidebar.write(f"**Entry:** {last['Close']:,.2f}")
    st.sidebar.success(f"**Target Profit:** {tp:,.2f}")
    st.sidebar.error(f"**Stop Loss:** {sl:,.2f}")

    # 5. DYNAMIC CHART
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.8, 0.2])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Market", increasing_line_color='#089981', decreasing_line_color='#f23645'
    ), row=1, col=1)

    # EMA 200
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], line=dict(color='#ff9800', width=1.5), name="EMA 200"), row=1, col=1)

    # Automated S&R Lines
    fig.add_hline(y=support, line_dash="dash", line_color="#00FFCC", opacity=0.6, annotation_text="SUPPORT", row=1, col=1)
    fig.add_hline(y=resistance, line_dash="dash", line_color="#FF3366", opacity=0.6, annotation_text="RESISTANCE", row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='#363a45', name="Volume"), row=2, col=1)

    # Layout
    fig.update_layout(
        height=800, template="plotly_dark", paper_bgcolor='#131722', plot_bgcolor='#131722',
        xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified"
    )
    fig.update_yaxes(side="right", gridcolor='#2a2e39')
    fig.update_xaxes(gridcolor='#2a2e39')

    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Masukkan simbol yang valid atau cek koneksi internet.")
