import threading
import pyupbit
import time
import queue
from collections import deque
import numpy as np
import pandas as pd

# 구매가 k-2 > k-1일 때, k-1의 시가와 k-1 저가 사이에 k 번째의 시가가 존재하면 k번째 가격에 구매
# 판매가 k-2 < k-1일 때, k-1의 시가와 k-1 고가 사이에 k 번째의 시가가 존재하면 k번째 가격에 판매

access = 'H9bA4XpjQZn0YcTQeHZxDD8FEniM3VyzGbUxf1VZ'
secret = 'HQB4M1kPFDGDv0hwziswJSnxzPJ3ixNdqyeCra6D'

class Consumer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q
        self.ticker = "KRW-BTC"

        self.buy = deque(maxlen=3)
        
        df = pyupbit.get_ohlcv(self.ticker, interval='minute15')
        self.buy.extend(df['open'])


    def run(self):
        price_curr = None
        hold_flag = False
        wait_flag = False

        upbit = pyupbit.Upbit(access, secret)
        print("autotrade start")
        cash = upbit.get_balance()
        print("보유현금:", cash)

        while True:
            try:
                if not self.q.empty():
                    
                    buy = []

                    A = self.buy.popleft()
                    B = self.buy.popleft()
                    C = self.buy.popleft()

                    buy.append(A)
                    buy.append(B)
                    buy.append(C)
                    print(A, B, C)
                    
                    price_open = self.q.get()
                    print(price_open)

                    if price_open != C:
                        self.buy.append(B)
                        self.buy.append(C)
                        self.buy.append(price_open)
                    
                    elif price_open == C:
                        self.buy.append(A)
                        self.buy.append(B)
                        self.buy.append(C)
                    
                    price_sell = price_open * 1.009
                    price_loss = price_open * 0.998
                    wait_flag = False

                price_curr = pyupbit.get_current_price(self.ticker)
                print(price_curr)
                print(buy[-3], buy[-2], buy[-1])
                if hold_flag == False and wait_flag == False and\
                    (A > B and B < C) or (B > C and C < price_open):
                    upbit.buy_markey_order(self.ticker, cash * 0.9995)
                    print('매수주문', ret)
                    time.sleep(1)
                    volume = upbit.get_balance(self.ticker)
                    ret = upbit.sell_limit_order(self.ticker, price_sell, volume)
                    print("매도주문", ret)
                    hold_flag = True
                
                if hold_flag == True:
                    uncomp = upbit.get_order(self.ticker)
                    if len(uncomp) == 0:
                        cash = upbit.get_balance()
                        print("매도완료", cash)
                        hold_flag = False
                        wait_flag = True
                    
                    elif len(uncomp) != 0 and price_curr <= price_loss:
                        uuid = ret['uuid'] 
                        print(uuid)
                        ret = upbit.cancel_order(uuid)
                        print(ret)
                        volume = upbit.get_balance(self.ticker)
                        ret = upbit.sell_limit_order(self.ticker, price_curr, volume)
                        uncomp = upbit.get_order(self.ticker)
                        
                        if len(uncomp) == 0:
                            cash = upbit.get_balance()
                            print("매도완료", cash)
                            hold_flag = False
                            wait_flag = True
        
            except:
                print("error")
       
            time.sleep(0.2)   

class Producer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q
    
    def run(self):
        while True:
            df = pyupbit.get_ohlcv("KRW-BTC", interval = 'minute15', to = '20221231 22:00:00')
            price = df.iloc[-1][0]
            self.q.put(price)
            time.sleep(0.1)

q = queue.Queue()
Producer(q).start()
Consumer(q).start()