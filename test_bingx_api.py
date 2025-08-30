# test_bingx_api.py
from exchange import get_exchange
from config import SYMBOL

def print_price():
    exchange = get_exchange()
    ticker = exchange.fetch_ticker(SYMBOL)
    print(f"[현재가] {SYMBOL}: {ticker['last']} USDT")

def print_balance():
    exchange = get_exchange()
    balance = exchange.fetch_balance()
    print("[잔액]")
    for coin, info in balance['total'].items():
        print(f"{coin}: {info} (free: {balance['free'][coin]}, used: {balance['used'][coin]})")

def print_orderbook():
    exchange = get_exchange()
    orderbook = exchange.fetch_order_book(SYMBOL)
    print(f"[호가 상위 5개] {SYMBOL}")
    print("매수:")
    for bid in orderbook['bids'][:5]:
        print(f"가격: {bid[0]}, 수량: {bid[1]}")
    print("매도:")
    for ask in orderbook['asks'][:5]:
        print(f"가격: {ask[0]}, 수량: {ask[1]}")

def print_trades():
    exchange = get_exchange()
    trades = exchange.fetch_trades(SYMBOL, limit=5)
    print(f"[최근 거래 내역] {SYMBOL}")
    for t in trades:
        print(f"가격: {t['price']}, 수량: {t['amount']}, 타임: {t['datetime']}")

if __name__ == "__main__":
    print_price()
    print()
    print_balance()
    print()
    print_orderbook()
    print()
    print_trades()

# To run this test, ensure you have set your BingX API keys in the .env file and execute: