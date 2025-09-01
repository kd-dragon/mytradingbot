# bot.py
import time
from strategy import (
    calculate_entry_price,
    calculate_levels,
    get_recent_candles,
    get_support_resistance,
    check_stoploss,
)
from logger import log
from config import POSITION_USD, LEVERAGE, SYMBOL
from exchange import get_exchange

exchange = get_exchange()

big_trend = 1  # 1: 상승, -1: 하락
position_open = False
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

        # 1️⃣ 현재 추세 판단 (단기/장기 이동평균선 교차)
        ma_short = sum(c[4] for c in candles[-5:]) / 5  # 최근 5캔들 종가 평균
        ma_long = sum(c[4] for c in candles[-20:]) / 20  # 최근 20캔들 종가 평균
        current_trend = 1 if ma_short > ma_long else -1
        log.info(f"현재 단기 이동평균: {ma_short}, 장기 이동평균: {ma_long}, 추세: {'상승' if current_trend == 1 else '하락'}")

        if current_trend == 0 or position_open:
            time.sleep(CHECK_INTERVAL)
            continue

        # 2️⃣ 과거 세그먼트 기반 저항/지지 확인
        support_resistance_levels = get_support_resistance(candles)

        # 3️⃣ 역추세 진입 후보 (양방향)
        entry_candidates = []

        entry_short = calculate_entry_price(1, support_resistance_levels, current_price)
        if entry_short:
            entry_candidates.append(('short', entry_short))

        entry_long = calculate_entry_price(-1, support_resistance_levels, current_price)
        if entry_long:
            entry_candidates.append(('long', entry_long))

        # 후보 여러개 → big_trend 우선
        selected_candidate = None
        for etype, price in entry_candidates:
            if (big_trend == 1 and etype == 'long') or (big_trend == -1 and etype == 'short'):
                selected_candidate = (etype, price)
                break

        # 우선 후보 없으면 첫 후보 선택
        if not selected_candidate and entry_candidates:
            selected_candidate = entry_candidates[0]

        closest_level = None
        min_distance = float('inf')

        for trend, high, low in support_resistance_levels:
            # current_price 기준으로 거리 계산
            if trend == 1:  # 상승세 → 저항 찾기
                distance = abs(current_price - high)
            else:  # 하락세 → 지지 찾기
                distance = abs(current_price - low)

            if distance < min_distance:
                min_distance = distance
                closest_level = (trend, high, low)

        log.info(f"현재가: {current_price}, 가장 가까운 레벨: {closest_level}, 거리: {min_distance}")

        log.info(f"진입 후보: {entry_candidates}, 선택된 진입: {selected_candidate}")

        # -----------------------------
        # 진입 주문 생성
        # -----------------------------
        if selected_candidate and not position_open:
            etype, entry_price = selected_candidate
            entry_type = etype
            size = max((POSITION_USD * LEVERAGE) / entry_price, 0.001)
            stop_loss, take_profit = calculate_levels(entry_price, 1 if entry_type == 'short' else -1)

            try:
                entry_order = exchange.create_order(
                    SYMBOL,
                    'limit',
                    'sell' if entry_type == 'short' else 'buy',
                    size,
                    entry_price
                )
                log.info(f"{entry_type} 진입 지정가 주문 걸림: 가격={entry_price}, 수량={size}")
                position_open = True
            except Exception as e:
                log.error(f"진입 주문 실패: {e}")
                entry_order = None
                position_open = False
                entry_type = None
                entry_price = None
                stop_loss = None
                take_profit = None
                size = None

        # -----------------------------
        # 포지션 체결 후 관리
        # -----------------------------
        if position_open:
            last_price = exchange.fetch_ticker(SYMBOL)['last']

            # 진입 주문 체결 확인
            if entry_order:
                open_orders = exchange.fetch_open_orders(SYMBOL)
                if all(o['id'] != entry_order['id'] for o in open_orders):
                    log.info("진입 주문 체결 완료")
                    entry_order = None
                    try:
                        takeprofit_order = exchange.create_order(
                            SYMBOL,
                            'limit',
                            'buy' if entry_type == 'short' else 'sell',
                            size,
                            take_profit
                        )
                        log.info(f"익절 지정가 주문 걸림: 가격={take_profit}, 수량={size}")
                    except Exception as e:
                        log.error(f"익절 주문 생성 실패: {e}")
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
                log.info(f"{entry_type} 손절! 현재가={last_price}, 기준={stop_loss}")
                # 상태 초기화
                position_open = False
                entry_type = None
                entry_price = None
                stop_loss = None
                take_profit = None
                size = None
                entry_order = None

            # 익절 체결 확인
            if takeprofit_order:
                open_orders = exchange.fetch_open_orders(SYMBOL)
                if all(o['id'] != takeprofit_order['id'] for o in open_orders):
                    log.info("익절 주문 체결 완료")
                    position_open = False
                    entry_type = None
                    entry_price = None
                    stop_loss = None
                    take_profit = None
                    size = None
                    entry_order = None
                    takeprofit_order = None

        time.sleep(CHECK_INTERVAL)

    except Exception as e:
        log.error(f"오류 발생: {e}")
        time.sleep(CHECK_INTERVAL)
