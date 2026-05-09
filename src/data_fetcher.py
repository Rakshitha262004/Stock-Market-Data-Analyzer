"""
Module: data_fetcher.py
Purpose: Fetch stock data from Yahoo Finance or load from CSV fallback
"""

import yfinance as yf
import pandas as pd
import os

def fetch_stock_data(ticker: str, start_date: str, end_date: str, save_csv: bool = True) -> pd.DataFrame:
    """
    Fetch historical OHLCV stock data using yfinance.
    Falls back to CSV if internet is unavailable.

    Args:
        ticker     : Stock symbol e.g. 'AAPL', 'RELIANCE.NS'
        start_date : 'YYYY-MM-DD'
        end_date   : 'YYYY-MM-DD'
        save_csv   : Whether to save fetched data to /data folder

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume
    """
    csv_path = f"data/{ticker}_{start_date}_{end_date}.csv"

    # Try loading from cached CSV first
    if os.path.exists(csv_path):
        print(f"[INFO] Loading cached data from {csv_path}")
        df = pd.read_csv(csv_path, index_col="Date", parse_dates=True)
        return df

    print(f"[INFO] Fetching {ticker} data from Yahoo Finance...")
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)

        if df.empty:
            raise ValueError(f"No data returned for ticker '{ticker}'. Check symbol.")

        # Flatten MultiIndex columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.index.name = "Date"

        if save_csv:
            os.makedirs("data", exist_ok=True)
            df.to_csv(csv_path)
            print(f"[INFO] Data saved to {csv_path}")

        return df

    except Exception as e:
        print(f"[ERROR] Could not fetch data: {e}")
        raise