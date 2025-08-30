# data.py
from exchange import get_exchange
from config import SYMBOL

def get_price():
    exchange = get_exchange()
    ticker = exchange.fetch_ticker(SYMBOL)
    return ticker["last"]

if __name__ == "__main__":
    print("현재가:", get_price())
