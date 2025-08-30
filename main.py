# bot.py
import time
from strategy import (
    calculate_entry_price,
    calculate_levels,
    get_recent_candles,
    find_trend_segments,
    place_limit_order,
    place_takeprofit_order,
    cancel_order,
    check_stoploss,
    check_takeprofit,
    get_balance
)
from logger import log
from config import POSITION_USD, LEVERAGE, SYMBOL, STOPLOSS_PERCENT, TAKEPROFIT_PERCENT
from exchange import get_exchange

exchange = get_exchange()

entry_type = None
stop_loss = None
take_profit = None
entry_price = None
entry_order = None
takeprofit_order = None
entry_status = None  # 'pending' / 'filled'
size = None

CHECK_INTERVAL = 60  # 1분마다 확인

while True:
    try:
        candles = get_recent_candles(days=3)  # 최근 3일치 15분봉
        current_price = exchange.fetch_ticker(SYMBOL)['last']

        trend_segments = find_trend_segments(candles)

        # 현재 가격 기준으로 진입할 구간 선택
        selected_segment = None
        for trend, segment in trend_segments:
            entry_price_candidate = calculate_entry_price(segment, trend, current_price)
            low = min(c[3] for c in segment)  # segment 저가
            high = max(c[2] for c in segment)  # segment 고가
            if low <= current_price <= high:
                selected_segment = (trend, segment, entry_price_candidate)
                break

        # -----------------------------
        # 진입 주문 생성
        # -----------------------------
        log.info(f"현재 추세: {'숏' if trend == 1 else '롱' if trend == -1 else '없음'}, 마지막 가격: {current_price}")
        # 진입
        if selected_segment and entry_type is None:
            trend, segment, entry_price = selected_segment
            stop_loss, take_profit = calculate_levels(entry_price, trend)
            entry_type = 'short' if trend == 1 else 'long'
            size = max((POSITION_USD * LEVERAGE) / entry_price, 0.001)

            try:
                entry_order = exchange.create_order(
                    SYMBOL,
                    'limit',
                    'sell' if entry_type == 'short' else 'buy',
                    size,
                    entry_price
                )
                log.info(f"{entry_type} 진입 지정가 주문 걸림: 가격={entry_price}, 수량={size}")
            except Exception as e:
                log.error(f"진입 지정가 주문 실패: {e}")
                entry_type = None
                entry_price = None
                stop_loss = None
                take_profit = None
                entry_order = None
                size = None

        # 현재가 확인
        if entry_type is not None:
            last_price = exchange.fetch_ticker(SYMBOL)['last']

            # 진입 지정가 미체결 & 캔들 범위 벗어나면 주문 취소
            if entry_order:
                low = min(c[3] for c in segment)
                high = max(c[2] for c in segment)
                if (trend == 1 and last_price > high) or (trend == -1 and last_price < low):
                    try:
                        exchange.cancel_order(entry_order['id'], SYMBOL)
                        log.info("진입 지정가 미체결, 캔들 범위 벗어나 주문 취소")
                    except Exception as e:
                        log.error(f"진입 주문 취소 실패: {e}")
                    entry_order = None
                    entry_type = None
                    entry_price = None
                    stop_loss = None
                    take_profit = None
                    size = None
                    continue

            # 진입 체결 후 익절 지정가 주문
            if entry_order is None and takeprofit_order is None and size:
                try:
                    tp_price = take_profit
                    takeprofit_order = exchange.create_order(
                        SYMBOL,
                        'limit',
                        'buy' if entry_type == 'short' else 'sell',
                        size,
                        tp_price
                    )
                    log.info(f"익절 지정가 주문 걸림: 가격={tp_price}, 수량={size}")
                except Exception as e:
                    log.error(f"익절 지정가 주문 실패: {e}")
                    takeprofit_order = None

            # 손절 체크
            if check_stoploss(entry_type, last_price, stop_loss):
                if takeprofit_order:
                    try:
                        exchange.cancel_order(takeprofit_order['id'], SYMBOL)
                        log.info("손절 발생, 익절 주문 취소")
                    except Exception as e:
                        log.error(f"익절 주문 취소 실패: {e}")
                    takeprofit_order = None
                entry_order = None
                entry_type = None
                entry_price = None
                stop_loss = None
                take_profit = None
                size = None
                log.info(f"{entry_type} 손절! 현재가={last_price}, 기준={stop_loss}")

            # 익절 체결 확인
            if takeprofit_order:
                open_orders = exchange.fetch_open_orders(SYMBOL)
                if all(o['id'] != takeprofit_order['id'] for o in open_orders):
                    log.info("익절 주문 체결 완료")
                    takeprofit_order = None
                    entry_order = None
                    entry_type = None
                    entry_price = None
                    stop_loss = None
                    take_profit = None
                    size = None

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        log.error(f"오류 발생: {e}")
        time.sleep(CHECK_INTERVAL)
