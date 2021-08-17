import time
import pyupbit
import datetime
from collections import deque

from pyupbit.exchange_api import get_tick_size

access = 'H9bA4XpjQZn0YcTQeHZxDD8FEniM3VyzGbUxf1VZ'
secret = 'HQB4M1kPFDGDv0hwziswJSnxzPJ3ixNdqyeCra6D'

def get_target_price(ticker):
    """매수 조건 판단"""
    price = deque(maxlen=3)
    df = pyupbit.get_ohlcv(ticker, interval="minute15")
    time.sleep(0.1)
    price.extend(df['open'])

    p = price.popleft()
    q = price.popleft()
    r = price.popleft()

    if p >= q and q < r:
        state = r
    
    else:
        state = -r

    return state   
    
def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_current_price(ticker)


# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
cash = upbit.get_balance()
print("보유현금:", cash)

ticker = "KRW-BTC"
hold_flag = False
wait_flag = False
loss_flag = False
print(ticker)
# 자동매매 시작
while True:
    try:
        if hold_flag == False and wait_flag == False and \
        get_target_price(ticker) > 0:
            target_price = get_target_price(ticker)
            current_price = get_current_price(ticker)
            buy_price = round(current_price * 1.0002, -3)
            sell_price = round(current_price * 1.002, -3)
            loss_price = round(current_price * 0.9981, -3)
            print("target_price:", target_price )
            print("current_price:", current_price )
            print("buy_price:", buy_price)
            print("sell_price:", sell_price )
            print("loss_price:", loss_price )
            if target_price <= current_price:
                ret = upbit.buy_limit_order(ticker, buy_price, cash * 0.9995/buy_price)
                print('매수주문', current_price, False, True)
                wait_flag = True
                time.sleep(0.1)

        if hold_flag == False and wait_flag == True:
            uncomp = upbit.get_order(ticker)
            changed_price = get_target_price(ticker)
            if len(uncomp) == 0:
                volume = upbit.get_balance(ticker)
                print("매수완료", volume, buy_price, True, False)
                hold_flag = True
                wait_flag = False
                time.sleep(0.1)

            elif len(uncomp) != 0 and target_price != changed_price:
                uuid = ret['uuid'] 
                print(target_price, changed_price, False, False)
                ret = upbit.cancel_order(uuid)
                wait_flag = False 
                time.sleep(0.1) 

        if hold_flag == True and wait_flag == False:
            volume = upbit.get_balance(ticker)
            ret = upbit.sell_limit_order(ticker, sell_price, volume)
            print("매도주문", "sell_price:", sell_price, True, True)
            hold_flag = True
            wait_flag = True
            loss_flag = True
            time.sleep(0.1)
        
        if hold_flag == True and wait_flag == True:
            uncomp = upbit.get_order(ticker)
            if len(uncomp) == 0:
                cash = upbit.get_balance()
                print("매도완료", cash, False, False)
                hold_flag = False
                wait_flag = False
                time.sleep(0.1)
            
            elif len(uncomp) != 0 and loss_flag == True and \
                loss_price >= get_current_price(ticker):
                uuid = ret['uuid'] 
                ret = upbit.cancel_order(uuid)
                print("losscut_on", get_current_price(ticker))
                volume = upbit.get_balance(ticker)
                ret = upbit.sell_limit_order(ticker, get_current_price(ticker), volume)
                print("익절주문", get_current_price(ticker))
                time.sleep(1)   
                uncomp = upbit.get_order(ticker)
                loss_flag = False

                if len(uncomp) == 0:
                    cash = upbit.get_balance()
                    print("익절완료", cash, False, False)
                    print('거래 중지')
                    while target_price == get_target_price(ticker):
                        A = A
                    hold_flag = False
                    wait_flag = False
                    print("거래 재개")
                
                elif len(uncomp) != 0:
                    loss_flag = True
                    print('익절실패', get_current_price(ticker))
                    time.sleep(1)

    except Exception as e:
        print(e)
        time.sleep(1)


