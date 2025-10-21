#!/usr/bin/env python3
"""
FastAPI wrapper for Yahoo Finance scraper.

Endpoints:
- POST /scrape: scrape historical data for one or more tickers over N months

Request body:
{
  "tickers": ["KO", "GE"],
  "months": 14,
  "save_csv": true
}

Response:
{
  "results": {
    "KO": {"rows": 288, "csv": "ko_historical_data.csv"},
    "GE": {"rows": 288, "csv": "ge_historical_data.csv"}
  }
}
"""

from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
import pandas as pd

from yahoo_finance_scraper import YahooFinanceScraper, construct_url


class ScrapeRequest(BaseModel):
    tickers: List[str] = Field(..., description="List of ticker symbols")
    months: int = Field(3, ge=1, le=120, description="Approx months of history to fetch")
    save_csv: bool = Field(True, description="Whether to save CSV files to disk")

    @validator("tickers")
    def validate_tickers(cls, v: List[str]) -> List[str]:
        cleaned = [t.strip() for t in v if t and t.strip()]
        if not cleaned:
            raise ValueError("At least one ticker is required")
        return cleaned


class ScrapeResult(BaseModel):
    rows: int
    csv: Optional[str] = None


class ScrapeResponse(BaseModel):
    results: Dict[str, ScrapeResult]


app = FastAPI(title="Yahoo Finance Scraper API", version="1.0.0")


@app.post("/scrape", response_model=ScrapeResponse)
def scrape(request: ScrapeRequest):
    scraper = YahooFinanceScraper(headless=True)
    results: Dict[str, ScrapeResult] = {}

    try:
        for ticker in request.tickers:
            url = construct_url(ticker, months=request.months)
            df: Optional[pd.DataFrame] = scraper.scrape_historical_data(url)

            if df is None or df.empty:
                # Represent as zero rows; client can handle failed tickers explicitly
                results[ticker] = ScrapeResult(rows=0, csv=None)
                continue

            filename = f"{ticker.lower()}_historical_data.csv" if request.save_csv else None
            if filename:
                scraper.save_to_csv(df, filename)

            results[ticker] = ScrapeResult(rows=len(df), csv=filename)

        return ScrapeResponse(results=results)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        scraper.close_driver()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)




