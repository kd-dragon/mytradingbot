# trader.py
from exchange import get_exchange
from config import SYMBOL, TRADE_AMOUNT

def create_order(side="buy", amount=TRADE_AMOUNT):
    exchange = get_exchange()

    if side == "buy":
        order = exchange.create_market_buy_order(SYMBOL, amount)
    else:
        order = exchange.create_market_sell_order(SYMBOL, amount)

    print("주문 결과:", order)
    return order

if __name__ == "__main__":
    create_order("buy")
