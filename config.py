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
POSITION_USD = float(os.getenv("POSITION_USD", "50"))  # $50로 매매
STOPLOSS_PERCENT = float(os.getenv("STOPLOSS_PERCENT", "0.02"))   # 2% 손절
TAKEPROFIT_PERCENT = float(os.getenv("TAKEPROFIT_PERCENT", "0.026"))  # 2.6% 익절

# 지정가 전략
ENTRY_PERCENT = 0.3  # 첫 캔들 몸통 기준 30% 위치 진입

# ===============================
# Bybit 테스트넷
USE_TESTNET = True
