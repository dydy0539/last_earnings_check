#!/usr/bin/env python3
"""
Comprehensive Stock Analysis for Tuesday Playbook Tickers
Analyzes stock performance, YTD/1-year returns, and post-earnings movements
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


def get_tuesday_tickers():
    """Extract tickers from the Tue column in Playbook sheet"""
    df = pd.read_excel('Playbook.xlsx', sheet_name='Playbook')
    tickers = df['Tue'].dropna().tolist()
    return [str(ticker).strip().upper() for ticker in tickers if ticker]


def fetch_stock_data(ticker, months=13):
    """Fetch historical stock data for the past N months"""
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*31)
        
        # Get historical data
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
        
        # Get earnings dates
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
        
        # Get the 4 most recent earnings dates
        earnings_dates_filtered = earnings_dates_filtered.head(4).sort_index(ascending=False)
        
        return earnings_dates_filtered
    except Exception as e:
        print(f"  ⚠️  Error fetching earnings info for {ticker}: {e}")
        return None


def calculate_ytd_return(hist):
    """Calculate year-to-date return"""
    try:
        # Find the first trading day of current year
        current_year = datetime.now().year
        year_start = pd.Timestamp(datetime(current_year, 1, 1))
        
        # Make sure hist.index is timezone-naive for comparison
        hist_index = hist.index.tz_localize(None) if hist.index.tz is not None else hist.index
        hist_copy = hist.copy()
        hist_copy.index = hist_index
        
        # Get data from year start
        year_data = hist_copy[hist_copy.index >= year_start]
        
        if len(year_data) < 2:
            return None
        
        start_price = year_data.iloc[0]['Close']
        current_price = year_data.iloc[-1]['Close']
        
        ytd_return = ((current_price - start_price) / start_price) * 100
        return ytd_return
    except Exception as e:
        print(f"  Error calculating YTD return: {e}")
        return None


def calculate_one_year_return(hist):
    """Calculate 1-year return"""
    try:
        if len(hist) < 2:
            return None
        
        # Get price from 1 year ago (approximately 252 trading days)
        one_year_ago_idx = min(252, len(hist) - 1)
        one_year_price = hist.iloc[-one_year_ago_idx]['Close']
        current_price = hist.iloc[-1]['Close']
        
        one_year_return = ((current_price - one_year_price) / one_year_price) * 100
        return one_year_return
    except Exception as e:
        print(f"  Error calculating 1-year return: {e}")
        return None


def calculate_post_earnings_return(ticker, hist, earnings_date, timing):
    """
    Calculate post-earnings return based on timing
    - Before market: compare same day to previous day
    - After market: compare next day to earnings day
    """
    try:
        earnings_datetime = pd.Timestamp(earnings_date).tz_localize(None)
        
        # Find the exact date or closest trading day
        available_dates = hist.index.tz_localize(None)
        
        # Find earnings date or next available trading day
        earnings_idx = None
        for i, date in enumerate(available_dates):
            if date >= earnings_datetime:
                earnings_idx = i
                break
        
        if earnings_idx is None:
            return None, None, None, None
        
        actual_earnings_date = available_dates[earnings_idx]
        
        # Determine if before or after market
        # If timing info is not available, assume after market close
        is_before_market = timing == 'Before Market Open' if timing else False
        
        if is_before_market:
            # Compare earnings day to previous day
            if earnings_idx == 0:
                return None, None, None, None
            
            prev_close = hist.iloc[earnings_idx - 1]['Close']
            earnings_close = hist.iloc[earnings_idx]['Close']
            pct_change = ((earnings_close - prev_close) / prev_close) * 100
            
            return pct_change, prev_close, earnings_close, 'Same Day vs Previous'
        else:
            # Compare next day to earnings day
            if earnings_idx >= len(hist) - 1:
                return None, None, None, None
            
            earnings_close = hist.iloc[earnings_idx]['Close']
            next_close = hist.iloc[earnings_idx + 1]['Close']
            pct_change = ((next_close - earnings_close) / earnings_close) * 100
            
            return pct_change, earnings_close, next_close, 'Next Day vs Earnings'
    except Exception as e:
        print(f"  Error calculating post-earnings return: {e}")
        return None, None, None, None


def analyze_ticker(ticker):
    """Comprehensive analysis for a single ticker"""
    print(f"\n{'='*80}")
    print(f"Analyzing: {ticker}")
    print(f"{'='*80}")
    
    # Fetch historical data
    hist = fetch_stock_data(ticker, months=13)
    if hist is None:
        return None
    
    print(f"  ✓ Fetched {len(hist)} days of historical data")
    
    # Calculate YTD and 1-year returns
    ytd_return = calculate_ytd_return(hist)
    one_year_return = calculate_one_year_return(hist)
    
    print(f"  ✓ YTD Return: {ytd_return:+.2f}%" if ytd_return else "  ⚠️  YTD Return: N/A")
    print(f"  ✓ 1-Year Return: {one_year_return:+.2f}%" if one_year_return else "  ⚠️  1-Year Return: N/A")
    
    # Get earnings information
    earnings_info = get_earnings_info(ticker)
    
    earnings_results = []
    if earnings_info is not None and not earnings_info.empty:
        print(f"  ✓ Found {len(earnings_info)} earnings dates since July 2024")
        
        for earnings_date, row in earnings_info.iterrows():
            # Check if there's timing information
            timing = None
            if 'EPS Estimate' in row.index:
                # yfinance doesn't directly provide before/after market info
                # We'll need to infer or use another method
                timing = 'After Market Close'  # Default assumption
            
            pct_change, price1, price2, comparison_type = calculate_post_earnings_return(
                ticker, hist, earnings_date, timing
            )
            
            if pct_change is not None:
                earnings_results.append({
                    'Date': earnings_date.strftime('%Y-%m-%d'),
                    'Timing': timing or 'Unknown',
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


def generate_report(results):
    """Generate comprehensive analysis report"""
    print(f"\n\n{'='*80}")
    print("COMPREHENSIVE ANALYSIS REPORT - TUESDAY PLAYBOOK TICKERS")
    print(f"{'='*80}\n")
    
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
            
            # Calculate average post-earnings return
            returns = [float(e['Return'].rstrip('%')) for e in result['earnings']]
            avg_return = sum(returns) / len(returns)
            positive_count = sum(1 for r in returns if r > 0)
            negative_count = sum(1 for r in returns if r < 0)
            
            print(f"\nAverage Post-Earnings Return: {avg_return:+.2f}%")
            print(f"Positive Moves: {positive_count}/{len(returns)} | Negative Moves: {negative_count}/{len(returns)}")
            print()
    
    # Save to CSV
    if summary_data:
        summary_df.to_csv('playbook_tuesday_summary.csv', index=False)
        print(f"\n✓ Summary saved to: playbook_tuesday_summary.csv")
    
    # Save detailed earnings data
    all_earnings = []
    for result in results:
        if result and result['earnings']:
            for earning in result['earnings']:
                earning['Ticker'] = result['ticker']
                all_earnings.append(earning)
    
    if all_earnings:
        earnings_df = pd.DataFrame(all_earnings)
        # Reorder columns
        cols = ['Ticker', 'Date', 'Timing', 'Comparison', 'Price Before', 'Price After', 'Return']
        earnings_df = earnings_df[cols]
        earnings_df.to_csv('playbook_tuesday_earnings_detail.csv', index=False)
        print(f"✓ Detailed earnings data saved to: playbook_tuesday_earnings_detail.csv")


def main():
    print("="*80)
    print("PLAYBOOK TUESDAY TICKERS - COMPREHENSIVE STOCK ANALYSIS")
    print("="*80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get tickers
    tickers = get_tuesday_tickers()
    print(f"Tickers to analyze: {', '.join(tickers)}")
    print(f"Total: {len(tickers)} tickers\n")
    
    # Analyze each ticker
    results = []
    for ticker in tickers:
        result = analyze_ticker(ticker)
        results.append(result)
    
    # Generate report
    generate_report(results)
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()

