import time
from exchange import get_exchange
from config import SYMBOL, STOPLOSS_PERCENT, TAKEPROFIT_PERCENT, ENTRY_PERCENT, USE_TESTNET
from logger import log

exchange = get_exchange()

def get_recent_candles(days=3):
    """최근 N일 15분봉 OHLCV 조회"""
    since = int(time.time() * 1000) - days * 24 * 60 * 60 * 1000
    candles = exchange.fetch_ohlcv(SYMBOL, timeframe='15m', since=since)
    # candles: [timestamp, open, high, low, close, volume]
    return candles

# --------------------------
# 과거 세그먼트 기반 저항/지지 확인 함수
# --------------------------
def get_support_resistance(candles, segment_length=5):
    """
    candles: 과거 캔들 리스트
    segment_length: 연속 캔들 세그먼트 길이
    return: 저항/지지 레벨 리스트 [(trend, high, low)]
    """
    levels = []
    for i in range(len(candles) - segment_length + 1):
        segment = candles[i:i + segment_length]
        opens = [c[1] for c in segment]
        highs = [c[2] for c in segment]
        lows = [c[3] for c in segment]
        closes = [c[4] for c in segment]

        # 추세 판단: 연속 양봉 → 상승, 연속 음봉 → 하락
        if all(closes[j] > opens[j] for j in range(segment_length)):
            levels.append((1, max(highs), min(lows)))  # 상승세: 최고가 저항, 최저가 지지
        elif all(closes[j] < opens[j] for j in range(segment_length)):
            levels.append((-1, max(highs), min(lows)))  # 하락세

    log.info(f"과거 세그먼트 기반 저항/지지 레벨: {levels}")
    return levels


# --------------------------
# 역추세 진입가 계산
# --------------------------
def calculate_entry_price(current_trend, support_resistance_levels, current_price, entry_percent=0.2):
    """
    current_trend: 현재 추세 1(상승) / -1(하락)
    support_resistance_levels: 과거 세그먼트에서 계산한 (trend, high, low) 리스트
    current_price: 현재 시장 가격
    """
    # 현재 추세가 상승이면 → 역추세 숏, 과거 상승 구간 저항 참고
    if current_trend == 1:
        # 과거 상승 구간의 최고가 중 가장 가까운 저항 레벨 선택
        resistance_levels = [high for trend, high, low in support_resistance_levels if trend == 1 and high > current_price]
        if not resistance_levels:
            return None  # 진입 기회 없음
        resistance_price = min(resistance_levels)
        entry_price = resistance_price + (resistance_price * entry_percent)

        if current_price >= entry_price:
            return entry_price
        else:
            return None  # 이미 내려와서 진입 무효

    else:  # 현재 추세 하락 → 역추세 롱, 과거 하락 구간 지지 참고
        support_levels = [low for trend, high, low in support_resistance_levels if trend == -1 and low < current_price]
        if not support_levels:
            return None
        support_price = max(support_levels)
        entry_price = support_price - (support_price * entry_percent)

        if current_price <= entry_price:
            return entry_price
        else:
            return None

def calculate_levels(entry_price, trend, big_trend):
    """
    entry_price : 진입가
    trend : 진입 방향 (1=숏, -1=롱)
    big_trend : 상위 추세 (1=상승, -1=하락)
    """
    # 기본 손절 비율
    stop_loss_percent = STOPLOSS_PERCENT

    # 익절 비율 조정: 상위 추세와 동일 → 1.5, 반대 → 1.3
    if trend == big_trend:
        take_profit_percent = TAKEPROFIT_PERCENT * 1.8
    else:
        take_profit_percent = TAKEPROFIT_PERCENT * 1.3

    if trend == 1:  # 숏
        stop_loss = entry_price * (1 + stop_loss_percent)
        take_profit = entry_price * (1 - take_profit_percent)
    else:           # 롱
        stop_loss = entry_price * (1 - stop_loss_percent)
        take_profit = entry_price * (1 + take_profit_percent)

    return stop_loss, take_profit

def place_limit_order(entry_type, entry_price, size):
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

def place_takeprofit_order(entry_type, size, take_profit):
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
