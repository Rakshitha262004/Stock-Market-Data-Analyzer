"""
app.py — Streamlit Dashboard
Stock Market Data Analyzer — Interactive Web Dashboard

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import date, timedelta
import os

# ─── Page Config ─────────────────────────────────────────────
st.set_page_config(
    page_title = "Stock Market Analyzer",
    page_icon  = "📈",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)

# ─── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }

    .metric-card {
        background: linear-gradient(135deg, #1a1d2e 0%, #16213e 100%);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px 20px;
        margin: 6px 0;
        text-align: center;
    }
    .metric-card .label {
        color: #8b949e;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .metric-card .value {
        color: #e6edf3;
        font-size: 22px;
        font-weight: 700;
    }
    .metric-card .value.positive { color: #3fb950; }
    .metric-card .value.negative { color: #f85149; }
    .metric-card .value.neutral  { color: #79c0ff; }

    .section-header {
        background: linear-gradient(90deg, #1f6feb22, transparent);
        border-left: 3px solid #1f6feb;
        padding: 10px 16px;
        border-radius: 0 8px 8px 0;
        margin: 20px 0 12px 0;
        color: #e6edf3;
        font-size: 16px;
        font-weight: 600;
    }
    .sidebar-brand {
        text-align: center;
        padding: 10px;
        background: linear-gradient(135deg, #1f6feb, #0d419d);
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .insight-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 8px 0;
        font-size: 14px;
        color: #c9d1d9;
        line-height: 1.6;
    }
    .signal-buy    { border-left: 4px solid #3fb950; }
    .signal-sell   { border-left: 4px solid #f85149; }
    .signal-neutral{ border-left: 4px solid #79c0ff; }
    div[data-testid="stMetricValue"] { font-size: 20px !important; }
</style>
""", unsafe_allow_html=True)

# ─── Helper Functions ─────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_data(ticker, start, end):
    """Load and cache stock data from yfinance"""
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if df.empty:
            return None, f"No data found for '{ticker}'. Please check the ticker symbol."
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df = df.dropna(subset=["Close"])
        return df, None
    except Exception as e:
        return None, str(e)

def compute_metrics(df):
    """Compute all financial metrics"""
    returns     = df["Close"].pct_change().dropna()
    daily_vol   = returns.std()
    annual_vol  = daily_vol * np.sqrt(252)
    mean_return = returns.mean() * 252
    risk_free   = 0.06
    sharpe      = (mean_return - risk_free) / annual_vol if annual_vol != 0 else 0
    cumulative  = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown    = (cumulative - rolling_max) / rolling_max
    max_dd      = drawdown.min()
    total_ret   = ((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]) * 100

    return {
        "total_return"       : round(total_ret, 2),
        "annual_volatility"  : round(annual_vol * 100, 2),
        "sharpe_ratio"       : round(sharpe, 3),
        "max_drawdown"       : round(max_dd * 100, 2),
        "best_day"           : round(returns.max() * 100, 2),
        "worst_day"          : round(returns.min() * 100, 2),
        "avg_daily_return"   : round(returns.mean() * 100, 4),
        "highest_close"      : round(df["Close"].max(), 2),
        "lowest_close"       : round(df["Close"].min(), 2),
        "start_price"        : round(float(df["Close"].iloc[0]), 2),
        "end_price"          : round(float(df["Close"].iloc[-1]), 2),
    }

def add_indicators(df):
    """Add SMA, EMA, RSI, Bollinger Bands to dataframe"""
    df = df.copy()

    # SMAs
    for w in [20, 50, 200]:
        if len(df) >= w:
            df[f"SMA_{w}"] = df["Close"].rolling(w).mean()

    # EMA
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

    # Bollinger Bands (20-day, ±2σ)
    df["BB_Mid"]   = df["Close"].rolling(20).mean()
    df["BB_Upper"] = df["BB_Mid"] + 2 * df["Close"].rolling(20).std()
    df["BB_Lower"] = df["BB_Mid"] - 2 * df["Close"].rolling(20).std()

    # RSI (14-day)
    delta  = df["Close"].diff()
    gain   = delta.where(delta > 0, 0).rolling(14).mean()
    loss   = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs     = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12       = df["Close"].ewm(span=12, adjust=False).mean()
    ema26       = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]  = ema12 - ema26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["Signal"]

    # Daily Return
    df["Daily_Return"] = df["Close"].pct_change() * 100

    return df

def generate_insights(df, metrics, ticker):
    """Generate text-based trading insights"""
    insights = []
    last_close = float(df["Close"].iloc[-1])

    # RSI Signal
    if "RSI" in df.columns:
        last_rsi = df["RSI"].dropna().iloc[-1]
        if last_rsi > 70:
            insights.append(("🔴 RSI Overbought",
                f"RSI at {last_rsi:.1f} — Stock may be overvalued. Watch for potential pullback.",
                "signal-sell"))
        elif last_rsi < 30:
            insights.append(("🟢 RSI Oversold",
                f"RSI at {last_rsi:.1f} — Stock may be undervalued. Possible buying opportunity.",
                "signal-buy"))
        else:
            insights.append(("🔵 RSI Neutral",
                f"RSI at {last_rsi:.1f} — Stock is in neutral zone.",
                "signal-neutral"))

    # Moving Average Signal
    if "SMA_50" in df.columns and "SMA_200" in df.columns:
        s50  = df["SMA_50"].dropna().iloc[-1]
        s200 = df["SMA_200"].dropna().iloc[-1]
        if s50 > s200:
            insights.append(("🟢 Golden Cross",
                f"SMA 50 ({s50:.2f}) is ABOVE SMA 200 ({s200:.2f}) — Bullish long-term trend.",
                "signal-buy"))
        else:
            insights.append(("🔴 Death Cross",
                f"SMA 50 ({s50:.2f}) is BELOW SMA 200 ({s200:.2f}) — Bearish long-term trend.",
                "signal-sell"))

    # Volatility
    ann_vol = metrics["annual_volatility"]
    if ann_vol > 50:
        insights.append(("⚡ High Volatility",
            f"Annual volatility is {ann_vol}%. This is a high-risk stock.",
            "signal-sell"))
    elif ann_vol < 20:
        insights.append(("🛡️ Low Volatility",
            f"Annual volatility is {ann_vol}%. This is a relatively stable stock.",
            "signal-buy"))
    else:
        insights.append(("📊 Moderate Volatility",
            f"Annual volatility is {ann_vol}%. Risk is within normal range.",
            "signal-neutral"))

    # Sharpe Ratio
    sharpe = metrics["sharpe_ratio"]
    if sharpe > 1:
        insights.append(("💰 Good Risk-Adjusted Return",
            f"Sharpe Ratio: {sharpe} — Returns justify the risk taken.",
            "signal-buy"))
    elif sharpe < 0:
        insights.append(("⚠️ Poor Risk-Adjusted Return",
            f"Sharpe Ratio: {sharpe} — Returns do not justify the risk.",
            "signal-sell"))

    # Total Return
    total_ret = metrics["total_return"]
    if total_ret > 0:
        insights.append(("📈 Positive Total Return",
            f"Stock gained {total_ret}% over the selected period.",
            "signal-buy"))
    else:
        insights.append(("📉 Negative Total Return",
            f"Stock lost {abs(total_ret)}% over the selected period.",
            "signal-sell"))

    return insights

# ─── PLOTLY CHART FUNCTIONS ───────────────────────────────────

def chart_candlestick(df, ticker):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.75, 0.25], vertical_spacing=0.02)
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="OHLC",
        increasing_line_color="#3fb950", decreasing_line_color="#f85149"
    ), row=1, col=1)
    if "Volume" in df.columns:
        colors = ["#3fb950" if c >= o else "#f85149"
                  for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"], name="Volume",
            marker_color=colors, opacity=0.7
        ), row=2, col=1)
    fig.update_layout(
        title=f"📈 {ticker} — Candlestick Chart",
        template="plotly_dark", height=550,
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#0e1117", plot_bgcolor="#161b22",
        font=dict(color="#c9d1d9"),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d")
    )
    return fig

def chart_moving_averages(df, ticker):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"],
        mode="lines", name="Close", line=dict(color="#79c0ff", width=2)))
    colors = {"SMA_20": "#FFD700", "SMA_50": "#FF6B6B",
              "SMA_200": "#A8FF78", "EMA_20": "#FF9ECD"}
    for col, col_color in colors.items():
        if col in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[col],
                mode="lines", name=col,
                line=dict(color=col_color, width=1.5, dash="dash")))
    fig.update_layout(
        title=f"📊 {ticker} — Moving Averages",
        template="plotly_dark", height=460,
        paper_bgcolor="#0e1117", plot_bgcolor="#161b22",
        font=dict(color="#c9d1d9")
    )
    return fig

def chart_bollinger_bands(df, ticker):
    fig = go.Figure()
    if "BB_Upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"],
            mode="lines", name="Upper Band",
            line=dict(color="#FF6B6B", width=1, dash="dot")))
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"],
            mode="lines", name="Lower Band",
            line=dict(color="#3fb950", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(63,185,80,0.06)"))
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_Mid"],
            mode="lines", name="Middle Band",
            line=dict(color="#FFD700", width=1, dash="dash")))
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"],
        mode="lines", name="Close", line=dict(color="#79c0ff", width=2)))
    fig.update_layout(
        title=f"🎯 {ticker} — Bollinger Bands",
        template="plotly_dark", height=460,
        paper_bgcolor="#0e1117", plot_bgcolor="#161b22",
        font=dict(color="#c9d1d9")
    )
    return fig

def chart_returns(df, ticker):
    if "Daily_Return" not in df.columns:
        return go.Figure()
    ret = df["Daily_Return"].dropna()
    fig = make_subplots(rows=1, cols=2,
        subplot_titles=["Daily Returns Over Time", "Return Distribution"])
    fig.add_trace(go.Bar(
        x=df.index, y=df["Daily_Return"],
        name="Daily Return %",
        marker_color=["#3fb950" if x >= 0 else "#f85149"
                      for x in df["Daily_Return"].fillna(0)]
    ), row=1, col=1)
    fig.add_trace(go.Histogram(
        x=ret, nbinsx=60, name="Distribution",
        marker_color="#7c3aed", opacity=0.85
    ), row=1, col=2)
    fig.update_layout(
        title=f"📉 {ticker} — Daily Returns Analysis",
        template="plotly_dark", height=430, showlegend=False,
        paper_bgcolor="#0e1117", plot_bgcolor="#161b22",
        font=dict(color="#c9d1d9")
    )
    return fig

def chart_rsi(df, ticker):
    if "RSI" not in df.columns:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"],
        mode="lines", name="RSI",
        line=dict(color="#FDB99B", width=2)))
    fig.add_hline(y=70, line_dash="dash", line_color="#f85149",
                  annotation_text="Overbought (70)", annotation_font_color="#f85149")
    fig.add_hline(y=30, line_dash="dash", line_color="#3fb950",
                  annotation_text="Oversold (30)", annotation_font_color="#3fb950")
    fig.add_hline(y=50, line_dash="dot", line_color="#8b949e")
    fig.update_layout(
        title=f"🔍 {ticker} — RSI (14-day)",
        template="plotly_dark", height=380,
        yaxis=dict(range=[0, 100]),
        paper_bgcolor="#0e1117", plot_bgcolor="#161b22",
        font=dict(color="#c9d1d9")
    )
    return fig

def chart_macd(df, ticker):
    if "MACD" not in df.columns:
        return go.Figure()
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.6, 0.4], vertical_spacing=0.04)
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"],
        mode="lines", name="Close", line=dict(color="#79c0ff", width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"],
        mode="lines", name="MACD", line=dict(color="#FFD700", width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Signal"],
        mode="lines", name="Signal", line=dict(color="#FF6B6B", width=1.5)), row=2, col=1)
    hist_colors = ["#3fb950" if v >= 0 else "#f85149"
                   for v in df["MACD_Hist"].fillna(0)]
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"],
        name="Histogram", marker_color=hist_colors, opacity=0.7), row=2, col=1)
    fig.update_layout(
        title=f"⚡ {ticker} — MACD",
        template="plotly_dark", height=500,
        paper_bgcolor="#0e1117", plot_bgcolor="#161b22",
        font=dict(color="#c9d1d9")
    )
    return fig

def chart_drawdown(df):
    returns    = df["Close"].pct_change().dropna()
    cum_ret    = (1 + returns).cumprod()
    roll_max   = cum_ret.cummax()
    drawdown   = (cum_ret - roll_max) / roll_max * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=drawdown.index, y=drawdown.values,
        mode="lines", name="Drawdown %",
        line=dict(color="#f85149", width=2),
        fill="tozeroy", fillcolor="rgba(248,81,73,0.15)"
    ))
    fig.update_layout(
        title="📉 Drawdown Analysis",
        xaxis_title="Date", yaxis_title="Drawdown (%)",
        template="plotly_dark", height=380,
        paper_bgcolor="#0e1117", plot_bgcolor="#161b22",
        font=dict(color="#c9d1d9")
    )
    return fig

# ─── SIDEBAR ─────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h2 style="color:white;margin:0;font-size:20px;">📈 StockAnalyzer</h2>
        <p style="color:#93c5fd;margin:4px 0 0 0;font-size:12px;">Market Intelligence Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### ⚙️ Configuration")

    ticker = st.text_input(
        "Stock Ticker Symbol",
        value="AAPL",
        help="Examples: AAPL, TSLA, MSFT, GOOGL, RELIANCE.NS, TCS.NS, INFY.NS"
    ).upper().strip()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date",
            value=date.today() - timedelta(days=730))
    with col2:
        end_date = st.date_input("End Date",
            value=date.today())

    # Quick presets
    st.markdown("**⚡ Quick Presets**")
    preset_cols = st.columns(3)
    if preset_cols[0].button("1Y"):
        start_date = date.today() - timedelta(days=365)
    if preset_cols[1].button("2Y"):
        start_date = date.today() - timedelta(days=730)
    if preset_cols[2].button("5Y"):
        start_date = date.today() - timedelta(days=1825)

    # Comparison
    st.markdown("---")
    st.markdown("### 📊 Compare Stocks")
    compare_input = st.text_input(
        "Add tickers (comma-separated)",
        placeholder="e.g. MSFT,GOOGL,TSLA",
        help="Compare performance against other stocks"
    )
    compare_tickers = [t.strip().upper() for t in compare_input.split(",") if t.strip()]

    st.markdown("---")
    show_raw = st.checkbox("Show Raw Data Table", value=False)

    st.markdown("---")
    st.markdown("""
    <div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:12px;font-size:11px;color:#8b949e;">
    ⚠️ <b>Disclaimer:</b> This tool is for <b>educational purposes only</b> and does not constitute financial advice. 
    Past performance does not guarantee future results. Always consult a certified financial advisor.
    </div>
    """, unsafe_allow_html=True)

# ─── MAIN CONTENT ────────────────────────────────────────────

st.markdown("""
<h1 style="color:#e6edf3;font-size:28px;margin-bottom:4px;">
    📈 Stock Market Data Analyzer
</h1>
<p style="color:#8b949e;font-size:14px;margin-bottom:24px;">
    Real-time market intelligence powered by Yahoo Finance | Educational Use Only
</p>
""", unsafe_allow_html=True)

# Load data
with st.spinner(f"Fetching data for {ticker}..."):
    df_raw, error = load_data(ticker, str(start_date), str(end_date))

if error:
    st.error(f"❌ {error}")
    st.stop()

if df_raw is None or df_raw.empty:
    st.warning("No data returned. Try a different ticker or date range.")
    st.stop()

# Add indicators
df = add_indicators(df_raw)
metrics = compute_metrics(df)
insights = generate_insights(df, metrics, ticker)

# ─── TOP KPI STRIP ───────────────────────────────────────────

st.markdown(f'<div class="section-header">📌 {ticker} — Key Performance Indicators</div>',
            unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)

def kpi_card(col, label, value, is_positive=None, suffix=""):
    css_class = ""
    if is_positive is True:   css_class = "positive"
    elif is_positive is False: css_class = "negative"
    else:                      css_class = "neutral"
    col.markdown(f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value {css_class}">{value}{suffix}</div>
    </div>
    """, unsafe_allow_html=True)

kpi_card(k1, "Current Price",  f"${metrics['end_price']}", None)
kpi_card(k2, "Total Return",   f"{metrics['total_return']}%",
         metrics["total_return"] >= 0)
kpi_card(k3, "Annual Volatility", f"{metrics['annual_volatility']}%",
         metrics["annual_volatility"] < 30)
kpi_card(k4, "Sharpe Ratio",   str(metrics["sharpe_ratio"]),
         metrics["sharpe_ratio"] > 1)
kpi_card(k5, "Max Drawdown",   f"{metrics['max_drawdown']}%", False)
kpi_card(k6, "Best Day",       f"+{metrics['best_day']}%", True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── PRICE CHART + STATS ──────────────────────────────────────

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Price & Volume",
    "📊 Moving Averages",
    "📉 Returns & Risk",
    "🔍 Technical Indicators",
    "💡 Insights",
    "📋 Data & Report"
])

with tab1:
    st.plotly_chart(chart_candlestick(df, ticker),
                    use_container_width=True)
    st.plotly_chart(chart_bollinger_bands(df, ticker),
                    use_container_width=True)

with tab2:
    st.plotly_chart(chart_moving_averages(df, ticker),
                    use_container_width=True)

    # MA Summary Table
    st.markdown('<div class="section-header">📌 Moving Average Summary</div>',
                unsafe_allow_html=True)
    ma_rows = []
    last_close = float(df["Close"].iloc[-1])
    for ma_col in ["SMA_20", "SMA_50", "SMA_200", "EMA_20"]:
        if ma_col in df.columns and not df[ma_col].dropna().empty:
            val = float(df[ma_col].dropna().iloc[-1])
            diff = ((last_close - val) / val) * 100
            signal = "🟢 Above" if last_close > val else "🔴 Below"
            ma_rows.append({
                "Indicator" : ma_col,
                "Value"     : round(val, 2),
                "Price vs MA": f"{diff:+.2f}%",
                "Signal"    : signal
            })
    if ma_rows:
        st.dataframe(pd.DataFrame(ma_rows), use_container_width=True)

with tab3:
    col_ret, col_dd = st.columns(2)
    with col_ret:
        st.plotly_chart(chart_returns(df, ticker),
                        use_container_width=True)
    with col_dd:
        st.plotly_chart(chart_drawdown(df),
                        use_container_width=True)

    # Risk metrics
    st.markdown('<div class="section-header">📊 Risk & Return Summary</div>',
                unsafe_allow_html=True)
    risk_c1, risk_c2, risk_c3, risk_c4 = st.columns(4)
    risk_c1.metric("Avg Daily Return", f"{metrics['avg_daily_return']}%")
    risk_c2.metric("Best Day",         f"+{metrics['best_day']}%")
    risk_c3.metric("Worst Day",        f"{metrics['worst_day']}%")
    risk_c4.metric("Max Drawdown",     f"{metrics['max_drawdown']}%")

with tab4:
    st.plotly_chart(chart_rsi(df, ticker), use_container_width=True)
    st.plotly_chart(chart_macd(df, ticker), use_container_width=True)

with tab5:
    st.markdown('<div class="section-header">💡 AI-Style Market Insights</div>',
                unsafe_allow_html=True)
    st.caption("⚠️ These insights are rule-based and for educational purposes only. Not financial advice.")

    for title, body, signal_class in insights:
        st.markdown(f"""
        <div class="insight-box {signal_class}">
            <b>{title}</b><br>{body}
        </div>
        """, unsafe_allow_html=True)

    # Comparison chart
    if compare_tickers:
        st.markdown('<div class="section-header">📊 Performance Comparison</div>',
                    unsafe_allow_html=True)
        all_tickers = [ticker] + compare_tickers
        fig_cmp = go.Figure()
        for t in all_tickers:
            df_t, err_t = load_data(t, str(start_date), str(end_date))
            if df_t is not None and not df_t.empty:
                norm = (df_t["Close"] / float(df_t["Close"].iloc[0])) * 100
                fig_cmp.add_trace(go.Scatter(
                    x=df_t.index, y=norm,
                    mode="lines", name=t
                ))
        fig_cmp.update_layout(
            title="Normalized Price Comparison (Base=100)",
            template="plotly_dark", height=450,
            yaxis_title="Normalized Price",
            paper_bgcolor="#0e1117", plot_bgcolor="#161b22",
            font=dict(color="#c9d1d9")
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

with tab6:
    # Full metrics table
    st.markdown('<div class="section-header">📋 Complete Analysis Report</div>',
                unsafe_allow_html=True)

    report_df = pd.DataFrame({
        "Metric": list(metrics.keys()),
        "Value":  list(metrics.values())
    })
    report_df["Metric"] = report_df["Metric"].str.replace("_", " ").str.title()
    st.dataframe(report_df, use_container_width=True)

    # Download report
    csv_data = report_df.to_csv(index=False)
    st.download_button(
        label      = "⬇️ Download Analysis Report (CSV)",
        data       = csv_data,
        file_name  = f"{ticker}_analysis_report.csv",
        mime       = "text/csv"
    )

    # Raw data
    if show_raw:
        st.markdown('<div class="section-header">📄 Raw Stock Data</div>',
                    unsafe_allow_html=True)
        st.dataframe(df_raw.tail(100), use_container_width=True)
        raw_csv = df_raw.to_csv()
        st.download_button(
            label      = "⬇️ Download Raw Data (CSV)",
            data       = raw_csv,
            file_name  = f"{ticker}_raw_data.csv",
            mime       = "text/csv"
        )

# ─── FOOTER ──────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#8b949e;font-size:12px;padding:10px;">
    📈 <b>Stock Market Data Analyzer</b> — Built with Python, Streamlit & Plotly<br>
    Data sourced from Yahoo Finance via yfinance | 
    ⚠️ <b>For educational purposes only. Not financial advice.</b>
</div>
""", unsafe_allow_html=True)