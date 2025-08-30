from exchange import get_exchange
from config import SYMBOL, STOPLOSS_PERCENT, TAKEPROFIT_PERCENT, POSITION_USD
from logger import log
import time

exchange = get_exchange()

def get_week_candles(exchange):
    one_week_ago = int(time.time()*1000) - 7*24*60*60*1000
    candles = exchange.fetch_ohlcv(SYMBOL, timeframe='15m', since=one_week_ago)
    return candles

def find_trend(candles):
    """
    최근 1주일 15분봉 캔들에서 5개 이상 연속 상승/하락 추세 찾기
    """
    direction_list = []
    for c in candles:
        open_price, close_price = c[1], c[4]
        if close_price > open_price:
            direction_list.append(1)
        elif close_price < open_price:
            direction_list.append(-1)
        else:
            direction_list.append(0)

    # 최근 5개 이상 연속 캔들 탐색
    for i in range(len(direction_list)-4):
        segment = direction_list[i:i+5]
        if segment == [1]*5:
            return 1, candles[i]   # 상승 추세, 시작 캔들
        elif segment == [-1]*5:
            return -1, candles[i]  # 하락 추세, 시작 캔들
    return 0, None

def calculate_levels(entry_price, trend, start_candle):
    """
    손절/익절 가격 계산
    """
    if trend == 1:  # 상승 추세 → 숏
        stop_loss = start_candle[2] * (1 + STOPLOSS_PERCENT)  # 시작 캔들 고가 +2%
        take_profit = entry_price * (1 - TAKEPROFIT_PERCENT)
    elif trend == -1:  # 하락 추세 → 롱
        stop_loss = start_candle[3] * (1 - STOPLOSS_PERCENT)  # 시작 캔들 저가 -2%
        take_profit = entry_price * (1 + TAKEPROFIT_PERCENT)
    else:
        stop_loss = None
        take_profit = None
    return stop_loss, take_profit

def check_stoploss(entry_type, last_price, stop_loss):
    if entry_type == 'long' and last_price < stop_loss:
        log.info(f"롱 손절! 현재가: {last_price}, 기준: {stop_loss}")
        return True
    elif entry_type == 'short' and last_price > stop_loss:
        log.info(f"숏 손절! 현재가: {last_price}, 기준: {stop_loss}")
        return True
    return False

def check_takeprofit(entry_type, last_price, take_profit):
    if entry_type == 'long' and last_price >= take_profit:
        log.info(f"롱 익절! 현재가: {last_price}, 기준: {take_profit}")
        return True
    elif entry_type == 'short' and last_price <= take_profit:
        log.info(f"숏 익절! 현재가: {last_price}, 기준: {take_profit}")
        return True
    return False

# 실제 주문 함수
def create_order(entry_type):
    # 현재가 조회
    ticker = exchange.fetch_ticker(SYMBOL)
    current_price = ticker['last']

    # 수량 계산: $50 기준
    size = POSITION_USD / current_price

    side = 'buy' if entry_type == 'long' else 'sell'
    try:
        order = exchange.create_order(SYMBOL, 'market', side, size)
        log.info(f"{entry_type} 주문 체결: {order}")
        return order
    except Exception as e:
        log.error(f"주문 실패: {e}")
        return None

# strategy.py
def get_balance():
    """
    선물 계정 잔액과 사용 중 자금 조회
    """
    try:
        balance = exchange.fetch_balance({'type':'future'})  # Bybit/BingX 선물 계정
        total = balance['total']
        used = balance['used']
        log.info(f"[잔액 확인] 총 잔액: {total}, 사용중: {used}")
        return total, used
    except Exception as e:
        log.error(f"잔액 조회 실패: {e}")
        return None, None

