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
                    
                    A = self.buy.popleft()
                    B = self.buy.popleft()
                    C = self.buy.popleft()
                    
                    price_open = self.q.get()
                    time.sleep(0.1)

                    if price_open != C:
                        self.buy.append(B)
                        self.buy.append(C)
                        self.buy.append(price_open)
                        
                        A = B
                        B = C
                        C = price_open

                    elif price_open == C:
                        self.buy.append(A)
                        self.buy.append(B)
                        self.buy.append(C)
                        
                    wait_flag = False
                    loss_flag = True

                price_curr = pyupbit.get_current_price(self.ticker)
                # print(price_curr)

                if hold_flag == False and wait_flag == False and\
                    A > B and B < C:
                    print(A, B, C, price_open)
                    price_buy = price_open
                    price_sell = round(price_open * 1.009, -3)
                    price_loss = round(price_open * 0.9982, -3)                     
                    ret = upbit.buy_limit_order(self.ticker, price_open, cash * 0.9995/price_open)
                    print('매수주문', ret)
                    time.sleep(1)
                    wait_flag = True

                if wait_flag == True:
                    uncomp = upbit.get_order(self.ticker)
                    if len(uncomp) == 0:
                        volume = upbit.get_balance(self.ticker)
                        print("매수완료", volume, price_buy)
                        hold_flag = True
                        wait_flag = False

                    elif len(uncomp) != 0 and price_buy != price_open:
                        uuid = ret['uuid'] 
                        print(uuid)
                        ret = upbit.cancel_order(uuid)
                        wait_flag = False  

                if hold_flag == True and wait_flag == False:
                    volume = upbit.get_balance(self.ticker)
                    ret = upbit.sell_limit_order(self.ticker, price_sell, volume)
                    print("매도주문", ret)
                    hold_flag = True
                    wait_flag = True
                    loss_flag = True
                
                if hold_flag == True and wait_flag == True and loss_flag == True:
                    uncomp = upbit.get_order(self.ticker)
                    print(uncomp)
                    if len(uncomp) == 0:
                        cash = upbit.get_balance()
                        print("매도완료", cash)
                        hold_flag = False
                        wait_flag = False
                    
                    elif len(uncomp) != 0 and price_curr <= price_loss:
                        uuid = ret['uuid'] 
                        print(uuid)
                        ret = upbit.cancel_order(uuid)
                        print("losscut_on", ret)
                        volume = upbit.get_balance(self.ticker)
                        ret = upbit.sell_limit_order(self.ticker, price_loss, volume)
                        print("익절주문", ret)
                        uncomp = upbit.get_order(self.ticker)
                        loss_flag = False
                        
                if hold_flag == True and wait_flag == True and len(uncomp) == 0 and loss_flag == False:
                    cash = upbit.get_balance()
                    print("익절완료", cash)
                    time.sleep(870)
                    hold_flag = False
                    wait_flag = False
                    loss_flag = True
                    
            except:
                print("error")
                time.sleep(10)
       
            time.sleep(0.2)   

class Producer(threading.Thread):
    def __init__(self, q):
        super().__init__()
        self.q = q
    
    def run(self):
        while True:
            df = pyupbit.get_ohlcv("KRW-BTC", interval = 'minute15')
            price = df.iloc[-1][0]
            self.q.put(price)
            time.sleep(0.1)

q = queue.Queue()
Producer(q).start()
Consumer(q).start()
