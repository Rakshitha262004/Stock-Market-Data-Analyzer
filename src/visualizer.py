"""
Module: visualizer.py
Purpose: Generate all Plotly charts and save as HTML/PNG
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import os

os.makedirs("outputs", exist_ok=True)

COLORS = {
    "close"  : "#00C9FF",
    "sma20"  : "#FFD700",
    "sma50"  : "#FF6B6B",
    "sma200" : "#A8FF78",
    "volume" : "#6C63FF",
    "return" : "#FF9A9E",
    "rsi"    : "#FDB99B",
}

def plot_price_and_volume(df: pd.DataFrame, ticker: str):
    """Candlestick price chart with volume bars"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.03,
        subplot_titles=[f"{ticker} — Closing Price", "Volume"]
    )

    # Candlestick
    if all(c in df.columns for c in ["Open", "High", "Low", "Close"]):
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"],
            low=df["Low"],   close=df["Close"],
            name="OHLC",
            increasing_line_color="#00C851",
            decreasing_line_color="#FF4444"
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"],
            mode="lines", name="Close",
            line=dict(color=COLORS["close"], width=2)
        ), row=1, col=1)

    # Volume
    if "Volume" in df.columns:
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            name="Volume",
            marker_color=COLORS["volume"],
            opacity=0.6
        ), row=2, col=1)

    fig.update_layout(
        title=f"📈 {ticker} — Price & Volume Analysis",
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        height=600,
        legend=dict(x=0.01, y=0.99)
    )
    fig.write_html(f"outputs/{ticker}_price_volume.html")
    print(f"[INFO] Chart saved: outputs/{ticker}_price_volume.html")
    return fig

def plot_moving_averages(df: pd.DataFrame, ticker: str):
    """Plot Close price with all available SMAs"""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"],
        mode="lines", name="Close Price",
        line=dict(color=COLORS["close"], width=2)
    ))

    for col, color in [("SMA_20", COLORS["sma20"]),
                        ("SMA_50", COLORS["sma50"]),
                        ("SMA_200", COLORS["sma200"])]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col],
                mode="lines", name=col,
                line=dict(color=color, width=1.5, dash="dash")
            ))

    fig.update_layout(
        title=f"📊 {ticker} — Moving Averages (SMA 20 / 50 / 200)",
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark",
        height=500
    )
    fig.write_html(f"outputs/{ticker}_moving_averages.html")
    print(f"[INFO] Chart saved: outputs/{ticker}_moving_averages.html")
    return fig

def plot_daily_returns(df: pd.DataFrame, ticker: str):
    """Plot daily return % as bar + histogram"""
    if "Daily_Return" not in df.columns:
        return

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Daily Returns Over Time", "Return Distribution"]
    )

    returns = df["Daily_Return"].dropna()

    # Time series bar
    fig.add_trace(go.Bar(
        x=df.index, y=df["Daily_Return"],
        name="Daily Return %",
        marker_color=df["Daily_Return"].apply(
            lambda x: "#00C851" if x >= 0 else "#FF4444"
        )
    ), row=1, col=1)

    # Histogram
    fig.add_trace(go.Histogram(
        x=returns, nbinsx=50,
        name="Distribution",
        marker_color=COLORS["return"],
        opacity=0.8
    ), row=1, col=2)

    fig.update_layout(
        title=f"📉 {ticker} — Daily Returns Analysis",
        template="plotly_dark",
        height=450,
        showlegend=False
    )
    fig.write_html(f"outputs/{ticker}_daily_returns.html")
    print(f"[INFO] Chart saved: outputs/{ticker}_daily_returns.html")
    return fig

def plot_rsi(df: pd.DataFrame, ticker: str):
    """Plot RSI with overbought/oversold bands"""
    if "RSI" not in df.columns:
        return

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI"],
        mode="lines", name="RSI",
        line=dict(color=COLORS["rsi"], width=2)
    ))

    # Overbought / Oversold reference lines
    fig.add_hline(y=70, line_dash="dash", line_color="red",
                  annotation_text="Overbought (70)")
    fig.add_hline(y=30, line_dash="dash", line_color="green",
                  annotation_text="Oversold (30)")
    fig.add_hline(y=50, line_dash="dot", line_color="gray")

    fig.update_layout(
        title=f"🔍 {ticker} — RSI (14-day)",
        xaxis_title="Date",
        yaxis_title="RSI",
        template="plotly_dark",
        height=400,
        yaxis=dict(range=[0, 100])
    )
    fig.write_html(f"outputs/{ticker}_rsi.html")
    print(f"[INFO] Chart saved: outputs/{ticker}_rsi.html")
    return fig