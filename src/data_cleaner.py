"""
Module: data_cleaner.py
Purpose: Clean and validate stock data
"""

import pandas as pd

def clean_stock_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean stock DataFrame:
    - Drop rows with missing Close prices
    - Ensure proper datetime index
    - Remove duplicate dates
    - Sort by date ascending

    Args:
        df: Raw stock DataFrame

    Returns:
        Cleaned DataFrame
    """
    print(f"[INFO] Raw data shape: {df.shape}")

    # Drop rows where Close is NaN (critical column)
    df = df.dropna(subset=["Close"])

    # Remove duplicate dates
    df = df[~df.index.duplicated(keep="first")]

    # Sort ascending
    df = df.sort_index(ascending=True)

    # Ensure index is datetime
    df.index = pd.to_datetime(df.index)

    # Keep only relevant columns
    cols_to_keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    df = df[cols_to_keep]

    print(f"[INFO] Cleaned data shape: {df.shape}")
    print(f"[INFO] Date range: {df.index[0].date()} to {df.index[-1].date()}")

    return df