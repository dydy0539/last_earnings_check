#!/usr/bin/env python3
"""
Earnings Date Stock Price Analysis
Analyzes stock price changes on earnings dates vs previous day
"""

import pandas as pd
from datetime import datetime
import re


def parse_date(date_str):
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(date_str.strip(), "%b %d, %Y")
    except ValueError:
        try:
            return datetime.strptime(date_str.strip(), "%B %d, %Y")
        except ValueError:
            print(f"Could not parse date: {date_str}")
            return None


def clean_price(price_str):
    """Clean price string and convert to float"""
    if pd.isna(price_str) or price_str == '-':
        return None
    # Remove commas and convert to float
    cleaned = re.sub(r'[,$]', '', str(price_str))
    try:
        return float(cleaned)
    except ValueError:
        return None


def analyze_earnings_impact():
    # Load the scraped data
    try:
        df = pd.read_csv('axp_historical_data.csv')
        print(f"Loaded {len(df)} rows of historical data")
    except FileNotFoundError:
        print("CSV file not found. Please run the scraper first.")
        return
    
    # Earnings dates
    earnings_dates = [
        "April 17, 2025",
        "January 24, 2025", 
        "October 18, 2024",
        "July 19, 2024",
        "April 19, 2024",
        "January 26, 2024",
        "October 20, 2023",
        "July 21, 2023"
    ]
    
    # Parse dates and convert to datetime
    df['Date_parsed'] = df['Date'].apply(parse_date)
    df['Close_clean'] = df['Close'].apply(clean_price)
    
    # Sort by date (newest first)
    df = df.sort_values('Date_parsed', ascending=False).reset_index(drop=True)
    
    results = []
    
    for earnings_date_str in earnings_dates:
        earnings_date = parse_date(earnings_date_str)
        if earnings_date is None:
            continue
            
        # Find the earnings date in our data
        earnings_row = df[df['Date_parsed'] == earnings_date]
        
        if earnings_row.empty:
            print(f"No data found for earnings date: {earnings_date_str}")
            continue
            
        earnings_idx = earnings_row.index[0]
        earnings_close = earnings_row['Close_clean'].iloc[0]
        
        if earnings_close is None:
            print(f"Invalid closing price for {earnings_date_str}")
            continue
        
        # Find previous trading day (next row since data is sorted newest first)
        if earnings_idx + 1 < len(df):
            prev_row = df.iloc[earnings_idx + 1]
            prev_close = prev_row['Close_clean']
            prev_date = prev_row['Date']
            
            if prev_close is not None:
                # Calculate percentage change
                pct_change = ((earnings_close - prev_close) / prev_close) * 100
                
                results.append({
                    'Earnings Date': earnings_date_str,
                    'Previous Date': prev_date,
                    'Previous Close': f"${prev_close:.2f}",
                    'Earnings Date Close': f"${earnings_close:.2f}",
                    'Price Change': f"${earnings_close - prev_close:.2f}",
                    'Percentage Change': f"{pct_change:+.2f}%"
                })
            else:
                print(f"Invalid previous closing price for {earnings_date_str}")
        else:
            print(f"No previous trading day data for {earnings_date_str}")
    
    # Create results DataFrame and display
    if results:
        results_df = pd.DataFrame(results)
        print("\n" + "="*80)
        print("AXP EARNINGS DATE STOCK PRICE ANALYSIS")
        print("="*80)
        print(results_df.to_string(index=False))
        
        # Save results
        results_df.to_csv('earnings_analysis_results.csv', index=False)
        print(f"\nResults saved to earnings_analysis_results.csv")
        
        # Summary statistics
        pct_changes = [float(row['Percentage Change'].rstrip('%')) for row in results]
        positive_changes = sum(1 for x in pct_changes if x > 0)
        negative_changes = sum(1 for x in pct_changes if x < 0)
        avg_change = sum(pct_changes) / len(pct_changes)
        
        print(f"\nSUMMARY:")
        print(f"Total earnings dates analyzed: {len(results)}")
        print(f"Positive price movements: {positive_changes}")
        print(f"Negative price movements: {negative_changes}")
        print(f"Average price change: {avg_change:+.2f}%")
    else:
        print("No earnings date analysis could be completed")


if __name__ == "__main__":
    analyze_earnings_impact()