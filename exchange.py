# exchange.py
import ccxt
from config import EXCHANGE_NAME, BYBIT_API_KEY, BYBIT_API_SECRET, BINGX_API_KEY, BINGX_API_SECRET, USE_TESTNET

def get_exchange():
    if EXCHANGE_NAME.lower() == "bybit":
        exchange = ccxt.bybit({
            "apiKey": BYBIT_API_KEY,
            "secret": BYBIT_API_SECRET,
            "enableRateLimit": True,
        })
        if USE_TESTNET:
            exchange.set_sandbox_mode(True)
        return exchange

    elif EXCHANGE_NAME.lower() == "bingx":
        exchange = ccxt.bingx({
            "apiKey": BINGX_API_KEY,
            "secret": BINGX_API_SECRET,
            "enableRateLimit": True,
        })
        return exchange

    else:
        raise ValueError(f"지원하지 않는 거래소: {EXCHANGE_NAME}")
