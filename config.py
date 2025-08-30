# config.py
from dotenv import load_dotenv
import os

load_dotenv()

# ===============================
# 거래소 설정
# ===============================
EXCHANGE_NAME = "bingx"  # "bybit" 또는 "bingx"

# Bybit API
BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

# BingX API
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
BINGX_API_SECRET = os.getenv("BINGX_API_SECRET")

# 거래 심볼
SYMBOL = "BTC/USDT"

# 리스크 관리
TRADE_AMOUNT = 0.001
STOP_LOSS = 0.005
TAKE_PROFIT = 0.01

# Bybit 테스트넷
USE_TESTNET = True
