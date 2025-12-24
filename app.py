import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. STYLE (TETAP KONSISTEN SEPERTI FOTO ANDA)
st.set_page_config(layout="wide", page_title="MEDALLION ALPHA X TRADINGVIEW")
st.markdown("""
    <style>
    .main { background-color: #131722; }
    div[data-testid="stMetric"] { background-color: #1e222d; border: 1px solid #363a45; padding: 15px; border-radius: 8px; }
    [data-testid="stMetricValue"] { font-size: 22px !important; color: #00FFCC !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ENGINE DATA ---
@st.cache_data(ttl=60)
def fetch_medallion_data(ticker, tf):
    if len(ticker) == 4 and ".JK" not in ticker: ticker = f"{ticker}.JK"
    elif "USDT" in ticker: ticker = ticker.replace("USDT", "-USD")
    elif len(ticker) >= 3 and "-" not in ticker and ".JK" not in ticker: ticker = f"{ticker}-USD"
    
    interval_map = {"15m": "15m", "30m": "30m", "1h": "1h", "4h": "1h", "1d": "1d"}
    p = "1mo" if tf in ["15m", "30m", "1h"] else "max"
    
    try:
        df = yf.download(ticker, period=p, interval=interval_map[tf], progress=False, auto_adjust=True)
        if df.empty: return pd.DataFrame(), ticker
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df.astype(float), ticker
    except: return pd.DataFrame(), ticker

# 2. SIDEBAR (TETAP SEPERTI FOTO)
st.sidebar.title("🏛️ MEDALLION ALPHA")
ticker_input = st.sidebar.text_input("Simbol", "BTC").upper()
tf_input = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"], index=2)

df, final_ticker = fetch_medallion_data(ticker_input, tf_input)

if not df.empty and len(df) > 30:
    # --- LOGIKA INTERNAL ---
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD'] = df['Close'].rolling(20).std()
    df['Z'] = (df['Close'] - df['MA20']) / df['STD']
    
    # ADX & MFI (Otak Akurasi)
    tr = pd.concat([df['High'] - df['Low'], (df['High'] - df['Close'].shift()).abs(), (df['Low'] - df['Close'].shift()).abs()], axis=1).max(axis=1)
    plus_dm = df['High'].diff().clip(lower=0)
    minus_dm = df['Low'].diff().clip(upper=0).abs()
    atr_14 = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr_14)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr_14)
    df['ADX'] = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di)).rolling(14).mean()
    
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0).rolling(14).sum()
    negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0).rolling(14).sum()
    df['MFI'] = 100 - (100 / (1 + (positive_flow / negative_flow)))
    
    last = df.iloc[-1]

    # 3. HEADER METRICS
    st.header(f"📊 {final_ticker} Terminal")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PRICE", f"{last['Close']:,.2f}")
    c2.metric("MFI (MONEY FLOW)", f"{last['MFI']:.1f}")
    c3.metric("ADX (STRENGTH)", f"{last['ADX']:.1f}")

    is_strong = last['ADX'] > 20
    if last['Z'] < -2.1 and is_strong and last['MFI'] < 35:
        sig_t, sig_c = "🚀 STRONG BUY", "#00FFCC"
    elif last['Z'] > 2.1 and is_strong and last['MFI'] > 65:
        sig_t, sig_c = "🔻 STRONG SELL", "#FF3366"
    else:
        sig_t, sig_c = "⚪ SEARCHING...", "#999999"
    c4.metric("ALGO SIGNAL", sig_t)

    # 4. SIDEBAR S&R & PLAN
    st.sidebar.markdown("---")
    st.sidebar.subheader("💎 ANGKA PETUNJUK S&R")
    sup, res = df['Low'].tail(50).min(), df['High'].tail(50).max()
    st.sidebar.write(f"**Resistance:** :red[{res:,.2f}]")
    st.sidebar.write(f"**Support:** :green[{sup:,.2f}]")

    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 TRADING PLAN")
    atr = tr.rolling(14).mean().iloc[-1]
    tp = last['Close'] + (atr * 2.5) if "BUY" in sig_t else last['Close'] - (atr * 2.5)
    sl = last['Close'] - (atr * 1.5) if "BUY" in sig_t else last['Close'] + (atr * 1.5)
    st.sidebar.markdown(f"**Status:** <span style='color:{sig_c}'>{sig_t}</span>", unsafe_allow_html=True)
    st.sidebar.write(f"**Entry:** {last['Close']:,.2f}")
    st.sidebar.success(f"**TP:** {tp:,.2f}")
    st.sidebar.error(f"**SL:** {sl:,.2f}")

    # 5. CHARTING (FULL INTERACTIVE TRADINGVIEW STYLE)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.85, 0.15])
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name="Price", increasing_line_color='#089981', decreasing_line_color='#f23645',
        increasing_fillcolor='#089981', decreasing_fillcolor='#f23645'
    ), row=1, col=1)
    
    # S&R Lines
    fig.add_hline(y=sup, line_dash="dash", line_color="#00FFCC", opacity=0.3, row=1, col=1)
    fig.add_hline(y=res, line_dash="dash", line_color="#FF3366", opacity=0.3, row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color='#363a45', name="Volume", opacity=0.5), row=2, col=1)

    # LAYOUT SETTINGS (Agar Mirip TradingView)
    fig.update_layout(
        height=800,
        template="plotly_dark",
        paper_bgcolor='#131722',
        plot_bgcolor='#131722',
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=10, b=10),
        hovermode="x unified",
        dragmode='pan' # Memungkinkan geser grafik (drag)
    )
    
    fig.update_yaxes(side="right", gridcolor='#2a2e39', zeroline=False)
    fig.update_xaxes(gridcolor='#2a2e39', zeroline=False)

    # Tombol Interaktif (Zoom, Pan, Reset)
    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': True,      # Zoom pakai scroll mouse
        'displayModeBar': True,  # Munculkan menu bar tradingview di atas chart
        'modeBarButtonsToAdd': ['drawline', 'drawrect', 'eraseshape'], # Tambah alat gambar sederhana
        'displaylogo': False
    })

    # 6. LIVE LOG (RIWAYAT SINYAL)
    st.markdown("---")
    st.subheader("📝 Live Algo Signal Log")
    if "LONG" in sig_t or "SHORT" in sig_t:
        st.write(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] **{sig_t}** terdeteksi pada harga {last['Close']:,.2f}")
    else:
        st.write("Menunggu konfirmasi sinyal akurat...")

else:
    st.info("Input simbol dan timeframe untuk memulai.")
