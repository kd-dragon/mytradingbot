# test_bingx_api.py
from exchange import get_exchange
from config import SYMBOL
from datetime import datetime
from zoneinfo import ZoneInfo

def print_price():
    exchange = get_exchange()
    ticker = exchange.fetch_ticker(SYMBOL)
    print(f"[현재가] {SYMBOL}: {ticker['last']} USDT")

def print_balance():
    exchange = get_exchange()
    spot_balance = exchange.fetch_balance()  # 현물 지갑 조회
    fut_balance = exchange.fetch_balance({'type': 'future'})
    print("[현물 지갑 잔고]")
    for asset, info in spot_balance['total'].items():
        if info > 0:
            print(f"{asset}: {info}")
    print("\n[선물 지갑 잔고]")
    for asset, info in fut_balance['total'].items():
        if info > 0:
            print(f"{asset}: {info}, 사용중: {fut_balance['used'][asset]}")

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
        # UTC 문자열 → datetime 객체
        utc_dt = datetime.fromisoformat(t['datetime'].replace("Z", "+00:00"))
        # 한국 시간(KST) 변환
        kst_dt = utc_dt.astimezone(ZoneInfo("Asia/Seoul"))
        print(f"가격: {t['price']}, 수량: {t['amount']}, 타임: {kst_dt.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    print_price()
    print()
    print_balance()
    print()
    print_orderbook()
    print()
    print_trades()

# To run this test, ensure you have set your BingX API keys in the .env file and execute: