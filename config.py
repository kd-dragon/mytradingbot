# config.py

# ===============================
# 거래소 설정
# ===============================
EXCHANGE_NAME = "bybit"   # "bybit" 또는 "bingx"

# API 키 (실계정 or 테스트 계정)
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"

# 거래 심볼
SYMBOL = "BTC/USDT"

# 리스크 관리 설정
TRADE_AMOUNT = 0.001   # BTC 수량
STOP_LOSS = 0.005      # 0.5% 손절
TAKE_PROFIT = 0.01     # 1% 익절

# Bybit 테스트넷 모드 (BingX에는 해당 없음)
USE_TESTNET = True
