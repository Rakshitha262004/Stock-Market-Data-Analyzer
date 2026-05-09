"""
Module: analyzer.py
Purpose: Calculate all financial metrics
"""

import pandas as pd
import numpy as np

def calculate_daily_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate daily percentage returns"""
    df = df.copy()
    df["Daily_Return"] = df["Close"].pct_change() * 100
    return df

def calculate_moving_averages(df: pd.DataFrame,
                               windows: list = [20, 50, 200]) -> pd.DataFrame:
    """
    Calculate Simple Moving Averages (SMA)

    Args:
        df     : Cleaned DataFrame with Close column
        windows: List of MA periods e.g. [20, 50, 200]

    Returns:
        DataFrame with MA columns added
    """
    df = df.copy()
    for w in windows:
        if len(df) >= w:
            df[f"SMA_{w}"] = df["Close"].rolling(window=w).mean()
            print(f"[INFO] SMA_{w} calculated")
        else:
            print(f"[WARNING] Not enough data for SMA_{w} (need {w} rows, have {len(df)})")
    return df

def calculate_volatility(df: pd.DataFrame) -> dict:
    """
    Calculate annualized volatility metrics

    Returns dict with:
    - daily_volatility
    - annual_volatility
    - sharpe_ratio (assuming risk-free rate = 6% for India, 4% for US)
    - max_drawdown
    - best_day / worst_day
    """
    returns = df["Close"].pct_change().dropna()

    daily_vol   = returns.std()
    annual_vol  = daily_vol * np.sqrt(252)         # 252 trading days/year
    mean_return = returns.mean() * 252              # Annualized mean return

    risk_free   = 0.06                              # Adjust: 0.04 for US stocks
    sharpe      = (mean_return - risk_free) / annual_vol if annual_vol != 0 else 0

    # Max Drawdown
    cumulative  = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown    = (cumulative - rolling_max) / rolling_max
    max_dd      = drawdown.min()

    # Cumulative return
    total_return = ((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]) * 100

    metrics = {
        "daily_volatility"   : round(daily_vol * 100, 4),
        "annual_volatility"  : round(annual_vol * 100, 2),
        "sharpe_ratio"       : round(sharpe, 4),
        "max_drawdown_pct"   : round(max_dd * 100, 2),
        "total_return_pct"   : round(total_return, 2),
        "best_day_return_pct": round(returns.max() * 100, 2),
        "worst_day_return_pct": round(returns.min() * 100, 2),
        "avg_daily_return_pct": round(returns.mean() * 100, 4),
        "highest_close"      : round(df["Close"].max(), 2),
        "lowest_close"       : round(df["Close"].min(), 2),
        "start_price"        : round(df["Close"].iloc[0], 2),
        "end_price"          : round(df["Close"].iloc[-1], 2),
    }

    return metrics

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Relative Strength Index (RSI)
    RSI > 70 → Overbought | RSI < 30 → Oversold
    """
    df = df.copy()
    delta  = df["Close"].diff()
    gain   = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss   = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs     = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df