# bot.py
import time
from strategy import (
    get_week_candles,
    find_trend,
    calculate_entry_price,
    calculate_levels,
    place_limit_order,
    place_takeprofit_order,
    cancel_order,
    check_stoploss,
    check_takeprofit,
    get_balance
)
from logger import log
from config import POSITION_USD
from exchange import get_exchange

exchange = get_exchange()

entry_type = None
stop_loss = None
take_profit = None
entry_price = None
entry_order = None
takeprofit_order = None
entry_status = None  # 'pending' / 'filled'

while True:
    try:
        candles = get_week_candles()
        trend, segment = find_trend(candles)
        last_price = exchange.fetch_ticker('BTC/USDT')['last']

        # -----------------------------
        # 진입 주문 생성
        # -----------------------------
        if trend != 0 and entry_type is None:
            entry_price = calculate_entry_price(segment, trend)
            stop_loss, take_profit = calculate_levels(entry_price, trend)
            entry_type = 'short' if trend == 1 else 'long'

            size = POSITION_USD / entry_price
            entry_order = place_limit_order(entry_type, entry_price, size)
            if entry_order:
                entry_status = 'pending'
                log.info(f"{entry_type} 지정가 주문 생성: {size} BTC @ {entry_price}")
            else:
                log.error("진입 주문 생성 실패")
                entry_type = None
                entry_price = None

        # -----------------------------
        # 진입 주문 체결 확인
        # -----------------------------
        if entry_order and entry_status == 'pending':
            orders = exchange.fetch_open_orders('BTC/USDT')
            filled = all(o['id'] != entry_order['id'] for o in orders)
            # 체결 완료
            if filled:
                entry_status = 'filled'
                takeprofit_order = place_takeprofit_order(entry_type, entry_price, size, take_profit)
                if takeprofit_order:
                    log.info(f"{entry_type} 익절 지정가 주문 생성: {size} BTC @ {take_profit}")
                else:
                    log.error("익절 주문 생성 실패")

            # 미체결 지정가 범위 벗어나면 취소
            elif (trend == 1 and last_price > segment[0][2]) or (trend == -1 and last_price < segment[0][3]):
                cancel_order(entry_order['id'])
                log.info("진입 지정가 범위 벗어나 취소")
                entry_order = None
                entry_type = None
                entry_price = None
                entry_status = None

        # -----------------------------
        # 체결 후 손절/익절 확인
        # -----------------------------
        if entry_status == 'filled':
            # 손절 체크
            if check_stoploss(entry_type, last_price, stop_loss):
                if takeprofit_order:
                    cancel_order(takeprofit_order['id'])
                    takeprofit_order = None
                log.info(f"{entry_type} 손절! 현재가: {last_price}, 기준: {stop_loss}")
                # 초기화
                entry_order = None
                entry_type = None
                entry_price = None
                stop_loss = None
                take_profit = None
                entry_status = None

            # 익절 체크
            elif check_takeprofit(entry_type, last_price, take_profit):
                log.info(f"{entry_type} 익절! 현재가: {last_price}, 기준: {take_profit}")
                takeprofit_order = None
                entry_order = None
                entry_type = None
                entry_price = None
                stop_loss = None
                take_profit = None
                entry_status = None

        # -----------------------------
        # 잔액/포지션 확인
        # -----------------------------
        get_balance()
        time.sleep(60)

    except Exception as e:
        log.error(f"오류 발생: {e}")
        time.sleep(60)
