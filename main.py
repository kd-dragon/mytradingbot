import time
from strategy import get_week_candles, find_trend, calculate_entry_price, calculate_levels, place_limit_order, place_takeprofit_order, cancel_order, cancel_order as cancel_takeprofit_order, check_stoploss, check_takeprofit, get_balance
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

while True:
    try:
        candles = get_week_candles()
        trend, segment = find_trend(candles)

        # 진입 지정가
        if trend != 0 and entry_type is None:
            entry_price = calculate_entry_price(segment, trend)
            stop_loss, take_profit = calculate_levels(entry_price, trend)
            entry_type = 'short' if trend == 1 else 'long'
            size = POSITION_USD / entry_price
            entry_order = place_limit_order(entry_type, entry_price)

        # 현재가 확인
        if entry_type is not None:
            last_price = exchange.fetch_ticker('BTC/USDT')['last']

            # 진입 지정가 미체결 & 캔들 범위 벗어나면 취소
            if entry_order and ((trend == 1 and last_price > segment[0][2]) or (trend == -1 and last_price < segment[0][3])):
                cancel_order(entry_order['id'])
                entry_order = None
                entry_type = None

            # 진입 체결 후 익절 지정가 주문 걸기
            if entry_order is None and takeprofit_order is None:
                takeprofit_order = place_takeprofit_order(entry_type, entry_price, size, take_profit)

            # 손절 체크
            if check_stoploss(entry_type, last_price, stop_loss):
                cancel_takeprofit_order(takeprofit_order['id'])
                takeprofit_order = None
                entry_order = None
                entry_type = None
                stop_loss = None
                take_profit = None
                entry_price = None

            # 익절 주문 체결 확인
            if takeprofit_order:
                orders = exchange.fetch_open_orders('BTC/USDT')
                if all(o['id'] != takeprofit_order['id'] for o in orders):
                    log.info("익절 주문 체결 완료")
                    takeprofit_order = None
                    entry_order = None
                    entry_type = None
                    stop_loss = None
                    take_profit = None
                    entry_price = None

        get_balance()
        time.sleep(60)

    except Exception as e:
        log.error(f"오류 발생: {e}")
        time.sleep(60)
