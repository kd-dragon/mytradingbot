# data.py
from exchange import get_exchange
from config import SYMBOL

def get_price():
    exchange = get_exchange()
    ticker = exchange.fetch_ticker(SYMBOL)
    return ticker["last"]

def get_ohlcv(timeframe="15m", limit=100):
    exchange = get_exchange()
    candles = exchange.fetch_ohlcv(SYMBOL, timeframe=timeframe, limit=limit)
    return candles
