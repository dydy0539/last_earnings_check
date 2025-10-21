#!/usr/bin/env python3
"""
Yahoo Finance Historical Data Scraper using Selenium
Scrapes historical stock data from Yahoo Finance
"""

import time
import argparse
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class YahooFinanceScraper:
    def __init__(self, headless=True):
        self.options = Options()
        if headless:
            self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.driver = None

    def start_driver(self):
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
    def close_driver(self):
        if self.driver:
            self.driver.quit()

    def scrape_historical_data(self, url, timeout=10):
        if not self.driver:
            self.start_driver()
        
        try:
            print(f"Loading URL: {url}")
            self.driver.get(url)
            
            # Wait for the table to load
            wait = WebDriverWait(self.driver, timeout)
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='history-table']")))
            
            # Wait a bit more for content to fully load
            time.sleep(2)
            
            # Find all rows in the table
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            
            if not rows:
                print("No data rows found")
                return None
            
            data = []
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 7:  # Ensure we have all required columns
                        # Yahoo Finance table structure: Date, Open, High, Low, Close, Adj Close, Volume
                        row_data = {
                            'Date': cells[0].text.strip(),
                            'Open': cells[1].text.strip(),
                            'High': cells[2].text.strip(),
                            'Low': cells[3].text.strip(),
                            'Close': cells[4].text.strip(),
                            'Adj_Close': cells[5].text.strip(),
                            'Volume': cells[6].text.strip()
                        }
                        data.append(row_data)
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue
            
            if data:
                df = pd.DataFrame(data)
                print(f"Successfully scraped {len(df)} rows of data")
                return df
            else:
                print("No data extracted")
                return None
                
        except TimeoutException:
            print(f"Timeout waiting for page to load after {timeout} seconds")
            return None
        except Exception as e:
            print(f"Error scraping data: {e}")
            return None

    def save_to_csv(self, df, filename):
        if df is not None:
            df.to_csv(filename, index=False)
            print(f"Data saved to {filename}")
        else:
            print("No data to save")


def get_unix_timestamps(months: int = 3):
    """Calculate Unix timestamps for N months ago and current date.
    Uses an approximate month length of 30 days which is sufficient
    for Yahoo Finance historical queries.
    """
    current_date = datetime.now()
    time2 = int(current_date.timestamp())
    # Approximate N months as 30 * N days
    days_back = max(1, int(30 * months))
    start_date = current_date - timedelta(days=days_back)
    time1 = int(start_date.timestamp())
    return time1, time2

def construct_url(ticker: str, months: int = 3):
    """Construct Yahoo Finance URL with ticker and time range."""
    time1, time2 = get_unix_timestamps(months)
    url = f"https://finance.yahoo.com/quote/{ticker.upper()}/history/?period1={time1}&period2={time2}"
    return url

def parse_args():
    parser = argparse.ArgumentParser(description="Yahoo Finance historical data scraper")
    parser.add_argument("--months", type=int, default=3, help="Number of months of history to fetch (approximate)")
    parser.add_argument("--tickers", type=str, default="", help="Comma or space separated list of tickers to fetch")
    parser.add_argument("ticker", nargs="?", default=None, help="Single ticker symbol if not using --tickers")
    return parser.parse_args()

def parse_ticker_list(tickers_arg: str) -> list:
    if not tickers_arg:
        return []
    # Split on commas and whitespace, filter empties
    raw = tickers_arg.replace(",", " ").split()
    return [t.strip() for t in raw if t.strip()]

def main():
    args = parse_args()
    months = max(1, args.months)

    tickers = parse_ticker_list(args.tickers)
    if not tickers and args.ticker:
        tickers = [args.ticker]

    # Backward compatible interactive prompt if still nothing provided
    if not tickers:
        fallback = input("Enter ticker symbol: ").strip()
        if fallback:
            tickers = [fallback]

    if not tickers:
        print("No ticker provided. Exiting.")
        return

    scraper = YahooFinanceScraper(headless=True)

    try:
        for ticker in tickers:
            # Construct URL
            url = construct_url(ticker, months)
            print(f"Constructed URL: {url}")

            data = scraper.scrape_historical_data(url)

            if data is not None:
                print("\nFirst 5 rows of scraped data:")
                print(data.head())

                # Save to CSV with ticker name
                filename = f"{ticker.lower()}_historical_data.csv"
                scraper.save_to_csv(data, filename)
            else:
                print(f"Failed to scrape data for {ticker}")
    finally:
        scraper.close_driver()


if __name__ == "__main__":
    main()