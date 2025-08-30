import time
from strategy import get_week_candles, find_trend, calculate_levels, create_order, check_stoploss, check_takeprofit, exchange, get_balance
from logger import log

entry_type = None
stop_loss = None
take_profit = None
entry_price = None


while True:
    try:
        candles = get_week_candles()
        trend, start_candle = find_trend(candles)

        # 진입
        if trend != 0 and entry_type is None:
            entry_price = candles[-1][4]
            entry_type = 'short' if trend == 1 else 'long'
            stop_loss, take_profit = calculate_levels(entry_price, trend, start_candle)
            create_order(entry_type)
            log.info(f"{entry_type} 진입 완료: 진입가={entry_price}, 손절={stop_loss}, 익절={take_profit}")

        # 현재가 확인
        if entry_type is not None:
            last_price = exchange.fetch_ticker('BTC/USDT')['last']

            # 손절 체크
            if check_stoploss(entry_type, last_price, stop_loss):
                entry_type = None
                stop_loss = None
                take_profit = None
                entry_price = None

            # 익절 체크
            elif check_takeprofit(entry_type, last_price, take_profit):
                entry_type = None
                stop_loss = None
                take_profit = None
                entry_price = None

        # 잔액/포지션 확인
        get_balance()

        time.sleep(60)  # 1분마다 체크

    except Exception as e:
        log.error(f"오류 발생: {e}")
        time.sleep(60)

# To run the bot, ensure you have set your API keys and configuration in the .env file and execute: