import time
from exchange import get_exchange
from config import SYMBOL, POSITION_USD, STOPLOSS_PERCENT, TAKEPROFIT_PERCENT, ENTRY_PERCENT, USE_TESTNET
from logger import log

exchange = get_exchange()

def get_week_candles():
    one_week_ago = int(time.time()*1000) - 7*24*60*60*1000
    candles = exchange.fetch_ohlcv(SYMBOL, timeframe='15m', since=one_week_ago)
    return candles

def find_trend(candles):
    direction_list = []
    for c in candles:
        open_price, close_price = c[1], c[4]
        if close_price > open_price:
            direction_list.append(1)
        elif close_price < open_price:
            direction_list.append(-1)
        else:
            direction_list.append(0)

    for i in range(len(direction_list)-4):
        segment = direction_list[i:i+5]
        if segment == [1]*5:
            return 1, candles[i:i+5]
        elif segment == [-1]*5:
            return -1, candles[i:i+5]
    return 0, None

def calculate_entry_price(candles_segment, trend):
    start_candle = candles_segment[0]
    open_price, close_price = start_candle[1], start_candle[4]
    body_length = abs(open_price - close_price)
    entry_offset = body_length * ENTRY_PERCENT
    if trend == 1:  # 상승 → 숏
        entry_price = close_price + entry_offset
    else:           # 하락 → 롱
        entry_price = close_price - entry_offset
    return entry_price

def calculate_levels(entry_price, trend):
    if trend == 1:  # 숏
        stop_loss = entry_price * (1 + STOPLOSS_PERCENT)
        take_profit = entry_price * (1 - TAKEPROFIT_PERCENT)
    else:           # 롱
        stop_loss = entry_price * (1 - STOPLOSS_PERCENT)
        take_profit = entry_price * (1 + TAKEPROFIT_PERCENT)
    return stop_loss, take_profit

def place_limit_order(entry_type, entry_price):
    ticker = exchange.fetch_ticker(SYMBOL)
    current_price = ticker['last']
    size = POSITION_USD / current_price
    if USE_TESTNET:
        log.info(f"[테스트 모드] {entry_type} 지정가 주문: {size:.6f} @ {entry_price}")
        return {'id':'TESTORDER','size':size,'price':entry_price}
    side = 'buy' if entry_type == 'long' else 'sell'
    try:
        order = exchange.create_order(SYMBOL, 'limit', side, size, entry_price)
        log.info(f"{entry_type} 지정가 주문 체결: {order}")
        return order
    except Exception as e:
        log.error(f"지정가 주문 실패: {e}")
        return None

def place_takeprofit_order(entry_type, entry_price, size, take_profit):
    if USE_TESTNET:
        log.info(f"[테스트 모드] {entry_type} 익절 지정가 주문: {size:.6f} @ {take_profit}")
        return {'id':'TESTTP','size':size,'price':take_profit}
    side = 'sell' if entry_type == 'long' else 'buy'
    try:
        order = exchange.create_order(SYMBOL, 'limit', side, size, take_profit)
        log.info(f"{entry_type} 익절 지정가 주문 체결 예약: {order}")
        return order
    except Exception as e:
        log.error(f"익절 지정가 주문 실패: {e}")
        return None

def cancel_order(order_id):
    try:
        exchange.cancel_order(order_id, SYMBOL)
        log.info(f"주문 취소: {order_id}")
    except Exception as e:
        log.error(f"주문 취소 실패: {e}")

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

def get_balance():
    try:
        balance = exchange.fetch_balance({'type':'future'})
        total = balance['total']
        used = balance['used']
        log.info(f"[잔액] 총: {total}, 사용중: {used}")
        return total, used
    except Exception as e:
        log.error(f"잔액 조회 실패: {e}")
        return None, None
