"""
Module: report_generator.py
Purpose: Generate CSV summary report
"""

import pandas as pd
import os

def generate_csv_report(metrics: dict, ticker: str, start: str, end: str):
    """Save risk and performance metrics as a CSV report"""
    os.makedirs("reports", exist_ok=True)

    report_data = {
        "Metric": list(metrics.keys()),
        "Value" : list(metrics.values())
    }

    df_report = pd.DataFrame(report_data)
    df_report.insert(0, "Ticker", ticker)
    df_report.insert(1, "Period", f"{start} to {end}")

    path = f"reports/{ticker}_analysis_report.csv"
    df_report.to_csv(path, index=False)
    print(f"[INFO] Report saved: {path}")
    return df_report