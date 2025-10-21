#!/usr/bin/env python3
"""
Daily Playbook Stock Analysis - Day-Aware Version
Automatically analyzes tickers based on the current day of the week
Runs Monday-Friday, analyzing the corresponding column from Playbook.xlsx
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import warnings
import sys
import os
warnings.filterwarnings('ignore')


def get_day_of_week():
    """Get the current day of the week"""
    days = ['Mon', 'Tue', 'Weds', 'Thur', 'Fri']
    weekday_index = datetime.now().weekday()  # 0=Monday, 4=Friday
    
    if weekday_index > 4:  # Saturday or Sunday
        print(f"Today is {datetime.now().strftime('%A')} - No analysis scheduled for weekends")
        return None
    
    return days[weekday_index]


def get_tickers_for_day(day_column):
    """Extract tickers from the specified day column in Playbook sheet"""
    try:
        df = pd.read_excel('Playbook.xlsx', sheet_name='Playbook')
        
        if day_column not in df.columns:
            print(f"❌ Column '{day_column}' not found in Playbook sheet")
            return []
        
        tickers = df[day_column].dropna().tolist()
        return [str(ticker).strip().upper() for ticker in tickers if ticker]
    except Exception as e:
        print(f"❌ Error reading Playbook.xlsx: {e}")
        return []


def fetch_stock_data(ticker, months=13):
    """Fetch historical stock data for the past N months"""
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*31)
        
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            print(f"  ⚠️  No historical data found for {ticker}")
            return None
        
        return hist
    except Exception as e:
        print(f"  ❌ Error fetching data for {ticker}: {e}")
        return None


def get_earnings_info(ticker):
    """Get earnings dates and timing (before/after market)"""
    try:
        stock = yf.Ticker(ticker)
        earnings_dates = stock.earnings_dates
        
        if earnings_dates is None or earnings_dates.empty:
            print(f"  ⚠️  No earnings data available for {ticker}")
            return None
        
        # Filter for dates from July 2024 onwards and get last 4
        july_2024 = pd.Timestamp(datetime(2024, 7, 1))
        
        # Make index timezone-naive for comparison
        earnings_index = earnings_dates.index.tz_localize(None) if earnings_dates.index.tz is not None else earnings_dates.index
        earnings_dates_copy = earnings_dates.copy()
        earnings_dates_copy.index = earnings_index
        
        earnings_dates_filtered = earnings_dates_copy[earnings_dates_copy.index >= july_2024]
        earnings_dates_filtered = earnings_dates_filtered.head(4).sort_index(ascending=False)
        
        return earnings_dates_filtered
    except Exception as e:
        print(f"  ⚠️  Error fetching earnings info for {ticker}: {e}")
        return None


def calculate_ytd_return(hist):
    """Calculate year-to-date return"""
    try:
        current_year = datetime.now().year
        year_start = pd.Timestamp(datetime(current_year, 1, 1))
        
        hist_index = hist.index.tz_localize(None) if hist.index.tz is not None else hist.index
        hist_copy = hist.copy()
        hist_copy.index = hist_index
        
        year_data = hist_copy[hist_copy.index >= year_start]
        
        if len(year_data) < 2:
            return None
        
        start_price = year_data.iloc[0]['Close']
        current_price = year_data.iloc[-1]['Close']
        
        ytd_return = ((current_price - start_price) / start_price) * 100
        return ytd_return
    except Exception as e:
        return None


def calculate_one_year_return(hist):
    """Calculate 1-year return"""
    try:
        if len(hist) < 2:
            return None
        
        one_year_ago_idx = min(252, len(hist) - 1)
        one_year_price = hist.iloc[-one_year_ago_idx]['Close']
        current_price = hist.iloc[-1]['Close']
        
        one_year_return = ((current_price - one_year_price) / one_year_price) * 100
        return one_year_return
    except Exception as e:
        return None


def calculate_post_earnings_return(ticker, hist, earnings_date, timing):
    """Calculate post-earnings return based on timing"""
    try:
        earnings_datetime = pd.Timestamp(earnings_date).tz_localize(None)
        available_dates = hist.index.tz_localize(None)
        
        earnings_idx = None
        for i, date in enumerate(available_dates):
            if date >= earnings_datetime:
                earnings_idx = i
                break
        
        if earnings_idx is None:
            return None, None, None, None
        
        actual_earnings_date = available_dates[earnings_idx]
        is_before_market = timing == 'Before Market Open' if timing else False
        
        if is_before_market:
            if earnings_idx == 0:
                return None, None, None, None
            
            prev_close = hist.iloc[earnings_idx - 1]['Close']
            earnings_close = hist.iloc[earnings_idx]['Close']
            pct_change = ((earnings_close - prev_close) / prev_close) * 100
            
            return pct_change, prev_close, earnings_close, 'Same Day vs Previous'
        else:
            if earnings_idx >= len(hist) - 1:
                return None, None, None, None
            
            earnings_close = hist.iloc[earnings_idx]['Close']
            next_close = hist.iloc[earnings_idx + 1]['Close']
            pct_change = ((next_close - earnings_close) / earnings_close) * 100
            
            return pct_change, earnings_close, next_close, 'Next Day vs Earnings'
    except Exception as e:
        return None, None, None, None


def analyze_ticker(ticker):
    """Comprehensive analysis for a single ticker"""
    print(f"\n{'='*80}")
    print(f"Analyzing: {ticker}")
    print(f"{'='*80}")
    
    hist = fetch_stock_data(ticker, months=13)
    if hist is None:
        return None
    
    print(f"  ✓ Fetched {len(hist)} days of historical data")
    
    ytd_return = calculate_ytd_return(hist)
    one_year_return = calculate_one_year_return(hist)
    
    print(f"  ✓ YTD Return: {ytd_return:+.2f}%" if ytd_return else "  ⚠️  YTD Return: N/A")
    print(f"  ✓ 1-Year Return: {one_year_return:+.2f}%" if one_year_return else "  ⚠️  1-Year Return: N/A")
    
    earnings_info = get_earnings_info(ticker)
    
    earnings_results = []
    if earnings_info is not None and not earnings_info.empty:
        print(f"  ✓ Found {len(earnings_info)} earnings dates since July 2024")
        
        for earnings_date, row in earnings_info.iterrows():
            timing = 'After Market Close'  # Default assumption
            
            pct_change, price1, price2, comparison_type = calculate_post_earnings_return(
                ticker, hist, earnings_date, timing
            )
            
            if pct_change is not None:
                earnings_results.append({
                    'Date': earnings_date.strftime('%Y-%m-%d'),
                    'Timing': timing,
                    'Comparison': comparison_type,
                    'Price Before': f"${price1:.2f}",
                    'Price After': f"${price2:.2f}",
                    'Return': f"{pct_change:+.2f}%"
                })
    else:
        print(f"  ⚠️  No earnings dates found since July 2024")
    
    return {
        'ticker': ticker,
        'ytd_return': ytd_return,
        'one_year_return': one_year_return,
        'earnings': earnings_results,
        'current_price': hist.iloc[-1]['Close'],
        'data_points': len(hist)
    }


def generate_report(results, day_of_week):
    """Generate comprehensive analysis report"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date_str = datetime.now().strftime('%Y%m%d')
    
    print(f"\n\n{'='*80}")
    print(f"DAILY PLAYBOOK ANALYSIS - {day_of_week.upper()} TICKERS")
    print(f"{'='*80}")
    print(f"Generated: {timestamp}\n")
    
    # Summary table
    summary_data = []
    for result in results:
        if result:
            summary_data.append({
                'Ticker': result['ticker'],
                'Current Price': f"${result['current_price']:.2f}",
                'YTD Return': f"{result['ytd_return']:+.2f}%" if result['ytd_return'] else 'N/A',
                '1-Year Return': f"{result['one_year_return']:+.2f}%" if result['one_year_return'] else 'N/A',
                'Earnings Analyzed': len(result['earnings'])
            })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        print("PERFORMANCE SUMMARY")
        print("-" * 80)
        print(summary_df.to_string(index=False))
        print()
    
    # Detailed earnings analysis for each ticker
    for result in results:
        if result and result['earnings']:
            print(f"\n{result['ticker']} - POST-EARNINGS PERFORMANCE")
            print("-" * 80)
            earnings_df = pd.DataFrame(result['earnings'])
            print(earnings_df.to_string(index=False))
            
            returns = [float(e['Return'].rstrip('%')) for e in result['earnings']]
            avg_return = sum(returns) / len(returns)
            positive_count = sum(1 for r in returns if r > 0)
            negative_count = sum(1 for r in returns if r < 0)
            
            print(f"\nAverage Post-Earnings Return: {avg_return:+.2f}%")
            print(f"Positive Moves: {positive_count}/{len(returns)} | Negative Moves: {negative_count}/{len(returns)}")
            print()
    
    # Save to CSV with date-specific filenames
    if summary_data:
        summary_filename = f'daily_analysis_{day_of_week.lower()}_{date_str}_summary.csv'
        summary_df.to_csv(summary_filename, index=False)
        print(f"\n✓ Summary saved to: {summary_filename}")
    
    # Save detailed earnings data
    all_earnings = []
    for result in results:
        if result and result['earnings']:
            for earning in result['earnings']:
                earning['Ticker'] = result['ticker']
                all_earnings.append(earning)
    
    if all_earnings:
        earnings_df = pd.DataFrame(all_earnings)
        cols = ['Ticker', 'Date', 'Timing', 'Comparison', 'Price Before', 'Price After', 'Return']
        earnings_df = earnings_df[cols]
        earnings_filename = f'daily_analysis_{day_of_week.lower()}_{date_str}_earnings.csv'
        earnings_df.to_csv(earnings_filename, index=False)
        print(f"✓ Detailed earnings data saved to: {earnings_filename}")


def main():
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("="*80)
    print("DAILY PLAYBOOK STOCK ANALYSIS - AUTOMATED RUN")
    print("="*80)
    print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %A')}")
    print()
    
    # Get the current day of week
    day_of_week = get_day_of_week()
    
    if day_of_week is None:
        print("⚠️  Skipping analysis - Not a weekday")
        sys.exit(0)
    
    print(f"📅 Today is {datetime.now().strftime('%A')} - Analyzing {day_of_week} column")
    print()
    
    # Get tickers for today
    tickers = get_tickers_for_day(day_of_week)
    
    if not tickers:
        print(f"⚠️  No tickers found for {day_of_week}")
        sys.exit(1)
    
    print(f"Tickers to analyze: {', '.join(tickers)}")
    print(f"Total: {len(tickers)} tickers\n")
    
    # Analyze each ticker
    results = []
    for ticker in tickers:
        result = analyze_ticker(ticker)
        results.append(result)
    
    # Generate report
    generate_report(results, day_of_week)
    
    print(f"\n{'='*80}")
    print("DAILY ANALYSIS COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()

