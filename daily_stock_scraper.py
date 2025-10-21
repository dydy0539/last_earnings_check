#!/usr/bin/env python3
"""
Daily Stock Data Scraper
Scrapes historical stock data for tickers organized by day of the week in Playbook.xlsx
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import sys
import warnings
import time
warnings.filterwarnings('ignore')


def get_day_column():
    """Get the column name for today's day of the week"""
    days = {
        'Monday': 'Mon',
        'Tuesday': 'Tue',
        'Wednesday': 'Wed',
        'Thursday': 'Thu',
        'Friday': 'Fri'
    }
    today = datetime.now().strftime('%A')
    return days.get(today, None), today


def get_tickers_for_today():
    """Extract tickers from the appropriate day column in Playbook sheet"""
    day_col, day_name = get_day_column()

    if day_col is None:
        print(f"Error: Script is designed to run Monday-Friday only. Today is {day_name}")
        return None, day_name

    try:
        df = pd.read_excel('Playbook.xlsx', sheet_name='Playbook')
        if day_col not in df.columns:
            print(f"Error: Column '{day_col}' not found in Playbook.xlsx")
            return None, day_name

        tickers = df[day_col].dropna().tolist()
        tickers = [str(ticker).strip().upper() for ticker in tickers if ticker]
        return tickers, day_name
    except Exception as e:
        print(f"Error reading Playbook.xlsx: {e}")
        return None, day_name


def scrape_stock_data(ticker, months=13, max_retries=3):
    """
    Scrape historical stock data for a ticker using yfinance

    Args:
        ticker: Stock ticker symbol
        months: Number of months of historical data to fetch
        max_retries: Maximum number of retry attempts

    Returns:
        DataFrame with historical data or None if error
    """
    for attempt in range(max_retries):
        try:
            print(f"\n{'='*60}")
            print(f"Fetching data for {ticker}... (Attempt {attempt+1}/{max_retries})")
            print(f"{'='*60}")

            # Create ticker (let yfinance handle session)
            stock = yf.Ticker(ticker)

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months*31)

            # Add delay to avoid rate limiting
            if attempt > 0:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"  Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

            # Get historical data
            hist = stock.history(start=start_date, end=end_date)

            if hist.empty:
                print(f"  ⚠️  No historical data found for {ticker}")
                if attempt < max_retries - 1:
                    continue
                return None

            # Reset index to make Date a column
            hist = hist.reset_index()

            # Format the data
            hist['Date'] = pd.to_datetime(hist['Date']).dt.strftime('%Y-%m-%d')

            # Select and rename columns to match standard format
            data = hist[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()

            print(f"  ✓ Successfully fetched {len(data)} days of data")
            print(f"  ✓ Date range: {data['Date'].iloc[0]} to {data['Date'].iloc[-1]}")
            print(f"  ✓ Latest close: ${data['Close'].iloc[-1]:.2f}")

            return data

        except Exception as e:
            print(f"  ⚠️  Error on attempt {attempt+1}: {e}")
            if attempt < max_retries - 1:
                continue
            else:
                print(f"  ❌ Failed after {max_retries} attempts")
                return None

    return None


def save_to_csv(data, ticker, day_name):
    """
    Save data to CSV file

    Args:
        data: DataFrame with stock data
        ticker: Stock ticker symbol
        day_name: Name of the day (e.g., 'Tuesday')
    """
    if data is None:
        return False

    try:
        # Create filename with ticker, day, and date
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"{ticker.lower()}_{day_name.lower()}_{date_str}.csv"

        data.to_csv(filename, index=False)
        print(f"  ✓ Data saved to: {filename}")
        return True

    except Exception as e:
        print(f"  ❌ Error saving data for {ticker}: {e}")
        return False


def main():
    print("="*60)
    print("DAILY STOCK DATA SCRAPER")
    print("="*60)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Get tickers for today
    tickers, day_name = get_tickers_for_today()

    if tickers is None:
        sys.exit(1)

    print(f"Day: {day_name}")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Total: {len(tickers)} ticker(s)")
    print()

    # Track results
    success_count = 0
    fail_count = 0

    # Scrape data for each ticker
    for ticker in tickers:
        data = scrape_stock_data(ticker, months=13)
        if save_to_csv(data, ticker, day_name):
            success_count += 1
        else:
            fail_count += 1

    # Print summary
    print(f"\n{'='*60}")
    print("SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Successful: {success_count}/{len(tickers)}")
    print(f"Failed: {fail_count}/{len(tickers)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
