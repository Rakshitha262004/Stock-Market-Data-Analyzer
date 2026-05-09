"""
main.py — Stock Market Data Analyzer
CLI entry point for running the full analysis pipeline.

Usage:
    python main.py
"""

from src.data_fetcher    import fetch_stock_data
from src.data_cleaner    import clean_stock_data
from src.analyzer        import (calculate_daily_returns,
                                  calculate_moving_averages,
                                  calculate_volatility,
                                  calculate_rsi)
from src.visualizer      import (plot_price_and_volume,
                                  plot_moving_averages,
                                  plot_daily_returns,
                                  plot_rsi)
from src.report_generator import generate_csv_report

def run_analysis(ticker: str, start: str, end: str):
    print("\n" + "="*60)
    print(f"  📈 STOCK MARKET DATA ANALYZER")
    print(f"  Ticker: {ticker} | Period: {start} → {end}")
    print("="*60 + "\n")

    # Step 1: Fetch
    df = fetch_stock_data(ticker, start, end)

    # Step 2: Clean
    df = clean_stock_data(df)

    # Step 3: Calculate metrics
    df = calculate_daily_returns(df)
    df = calculate_moving_averages(df, windows=[20, 50, 200])
    df = calculate_rsi(df, period=14)
    metrics = calculate_volatility(df)

    # Step 4: Print summary
    print("\n📊 ANALYSIS SUMMARY")
    print("-" * 40)
    for k, v in metrics.items():
        print(f"  {k:<28} : {v}")

    # Step 5: Visualize
    plot_price_and_volume(df, ticker)
    plot_moving_averages(df, ticker)
    plot_daily_returns(df, ticker)
    plot_rsi(df, ticker)

    # Step 6: Report
    generate_csv_report(metrics, ticker, start, end)

    print("\n✅ Analysis complete! Check /outputs and /reports folders.")

if __name__ == "__main__":
    # ── Edit these values ──
    TICKER     = "AAPL"          # Try: TSLA, MSFT, RELIANCE.NS, TCS.NS
    START_DATE = "2022-01-01"
    END_DATE   = "2024-12-31"
    # ──────────────────────
    run_analysis(TICKER, START_DATE, END_DATE)