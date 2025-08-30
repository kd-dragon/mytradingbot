# main.py
from data import get_price
from trader import create_order

def main():
    price = get_price()
    print(f"현재가: {price} USDT")

    if price < 60000:
        print("조건 충족 → 매수 실행")
        create_order("buy")
    else:
        print("조건 불충족 → 대기")

if __name__ == "__main__":
    main()
