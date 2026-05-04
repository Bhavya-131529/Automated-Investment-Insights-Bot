import yfinance as yf
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import os
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

def get_stock_price(ticker: str):
    """Fetch current price and 1y return for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get("regularMarketPrice") or info.get("currentPrice")
        
        # Get historical data for 1y return
        hist = stock.history(period="1y")
        if not hist.empty:
            start_price = hist['Close'].iloc[0]
            end_price = hist['Close'].iloc[-1]
            one_year_return = ((end_price - start_price) / start_price) * 100
        else:
            one_year_return = None
            
        return {
            "ticker": ticker,
            "price": current_price,
            "1y_return": one_year_return,
            "currency": info.get("currency", "USD"),
            "name": info.get("longName", ticker)
        }
    except Exception as e:
        return {"error": str(e)}

def get_market_indicators():
    """Fetch basic market indicators from Alpha Vantage (if key provided) or fallback."""
    if not ALPHA_VANTAGE_API_KEY:
        return {"info": "Alpha Vantage API key not provided. Using fallback data."}
    
    try:
        ts = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
        # Just an example: get SPY data
        data, meta_data = ts.get_intraday(symbol='SPY', interval='60min', outputsize='compact')
        return {"market": "SPY", "last_close": data['4. close'].iloc[-1]}
    except Exception as e:
        return {"error": str(e)}
