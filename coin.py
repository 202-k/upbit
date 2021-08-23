import pyupbit
import time
import csv
import datetime
import requests
from slacker import Slacker


class MyUpbit():
    def __init__(self):
        self._access = "5TjiFFJzxBFZSCaIcAURIK5uyP4jsKc1iAJCxuQ2"
        self._secret = "duPIHHQDno4SSIxjWPFk5uCR0v5JvtxjksAr9h8Z"
        self.upbit = pyupbit.Upbit(self._access, self._secret)
        self.money_per_coin = 5205
        self.fee = 0.0005
        self.profit_cut = 0.02
        self.loss_cut = 0.03

    def check_hold(self, ticker):
        if self.upbit.get_balance(ticker.ticker):
            ticker.hold = True
            ticker.buy_price = self.upbit.get_avg_buy_price(ticker.ticker)
            ticker.hold_amount = self.upbit.get_amount(ticker.ticker, contain_req=True)

    def buy_coin(self, ticker):
        self.total_money = self.upbit.get_balance()
        if (ticker.hold == False) and (self.total_money >= self.money_per_coin * (1 + self.fee)):
            data = pyupbit.get_ohlcv(ticker=ticker.ticker, interval="minute15", count=25)
            data['clo20'] = round(data['close'].rolling(window=20).mean(), 2)
            price = pyupbit.get_current_price(ticker.ticker)
            if price <= data['clo20'][-1] * 0.98:
                print("!!!!!!!!!!buy!!!!!!!!!", data['clo20'][-1] * 0.98, price)
                volume = self.money_per_coin/price
                self.upbit.buy_limit_order(ticker=ticker.ticker, price=price, volume=volume)
                ticker.hold = True
                ticker.buy_price = price
                ticker.hold_amount = self.upbit.get_amount(ticker.ticker, contain_req=True)
                ticker.record_trade()
                ticker.send_slack()

    def sell_coin(self, ticker):
        if ticker.hold == True:
            price = pyupbit.get_current_price(ticker.ticker)
            volume = self.upbit.get_balance(ticker=ticker.ticker)
            if price >= ticker.buy_price * (1 + self.profit_cut) or price <= ticker.buy_price * (1 - self.loss_cut):
                self.upbit.sell_market_order(ticker=ticker.ticker, volume=volume)
                ticker.sell_price = price
                ticker.hold = False
                ticker.record_trade()
                ticker.send_slack()
                ticker.buy_price = None
                ticker.hold_amount = None
                ticker.sell_price = None
class Coin:
    def __init__(self, ticker):
        self.ticker = ticker
        self.hold = False


    def record_trade(self):
        f = open(self.ticker + ".csv", 'a', newline="\n")
        wr = csv.writer(f)
        if self.hold == True:
            print(self.ticker, 'buy record')
            wr.writerow(
                [datetime.datetime.now(), self.ticker, 'buy', self.buy_price * (1 + self.fee), self.hold_amount])
        else:
            print(self.ticker, 'sell record')
            wr.writerow(
                [datetime.datetime.now(), self.ticker, 'sell', self.sell_price * (1 - self.fee), self.hold_amount])
        f.close()

    def load_tickers(self):
        f = open("tickers", 'w', newline='\n')
        tickers = pyupbit.get_tickers("KRW")
        for k in range(len(tickers)):
            f.write(tickers[k] + '\n')
        f.close()

    def send_slack(self):
        token = "xoxb-2403642842261-2419294353969-lzGW6PxiAy3RQDUsxA0G7LyI"
        if self.hold == True:
            text = str(self.ticker) + ' buy' + '\n price' + str(self.buy_price * (self.hold_amount))
        else:
            text = str(self.ticker) + ' sell' + '\n price' + str(self.buy_price * (self.hold_amount))
        requests.post("https://slack.com/api/chat.postMessage",
                      headers={
                          "Authorization": "Bearer " + token},
                      data={"channel": "#coin", "text": text}
                      )


if __name__ == '__main__':
    # btc = Coin("KRW-BTC")
    # btc.load_tickers()
    f = open(file="tickers", mode='r')
    coins = []
    while True:
        line = f.readline()
        if not line:
            break
        line = line.strip()
        coins.append(Coin(line))
    f.close()
    upbit = MyUpbit()
    while True:
        for i in range(len(coins)):
            upbit.check_hold(coins[i])
            if coins[i].hold:
                upbit.sell_coin(coins[i])
            else:
                upbit.buy_coin(coins[i])
