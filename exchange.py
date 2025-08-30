# exchange.py
import ccxt
from config import EXCHANGE_NAME, API_KEY, API_SECRET, USE_TESTNET

def get_exchange():
    """선택된 거래소 객체 반환 (ccxt)"""
    if EXCHANGE_NAME.lower() == "bybit":
        exchange = ccxt.bybit({
            "apiKey": API_KEY,
            "secret": API_SECRET,
            "enableRateLimit": True,
        })
        if USE_TESTNET:
            exchange.set_sandbox_mode(True)
        return exchange

    elif EXCHANGE_NAME.lower() == "bingx":
        exchange = ccxt.bingx({
            "apiKey": API_KEY,
            "secret": API_SECRET,
            "enableRateLimit": True,
        })
        # BingX는 sandbox/testnet 없음
        return exchange

    else:
        raise ValueError(f"지원하지 않는 거래소: {EXCHANGE_NAME}")
