import pyupbit
import time
import csv
import datetime
import requests
from slacker import Slacker


class Coin:
    def __init__(self, ticker):
        self.ticker = ticker
        self._access = "5TjiFFJzxBFZSCaIcAURIK5uyP4jsKc1iAJCxuQ2"
        self._secret = "duPIHHQDno4SSIxjWPFk5uCR0v5JvtxjksAr9h8Z"
        self.upbit = pyupbit.Upbit(self._access, self._secret)
        self.money_per_coin = 5000
        self.hold = False
        self.fee = 0.0005
        self.profit_cut = 0.02
        self.loss_cut = 0.03
        self.total_money = self.upbit.get_balance()

    def buy_coin(self):
        if self.upbit.get_balance(self.ticker):
            self.hold = True
            self.buy_price = self.upbit.get_avg_buy_price(self.ticker)
            self.hold_amount = self.upbit.get_amount(self.ticker, contain_req=True)
        if (self.hold == False) and (self.total_money >= self.money_per_coin * (1 + self.fee)):
            data = pyupbit.get_ohlcv(ticker=self.ticker, interval="minute15", count=25)
            data['clo20'] = round(data['close'].rolling(window=20).mean(), 2)
            price = pyupbit.get_current_price(self.ticker)
            if price <= data['clo20'][-1] * 0.98:
                print("!!!!!!!!!!buy!!!!!!!!!", data['clo20'][-1] * 0.98, price)
                self.upbit.buy_market_order(ticker=self.ticker, price=self.money_per_coin)
                self.hold = True
                self.buy_price = price
                self.hold_amount = self.upbit.get_amount(self.ticker, contain_req=True)
                self.record_trade()
                self.send_slack()
            # else:
            #     print("No", data['clo20'][-1] * 0.98, price)

    def sell_coin(self):
        if self.hold == True:
            price = pyupbit.get_current_price(self.ticker)
            volume = self.upbit.get_balance(ticker=self.ticker)
            if price >= self.buy_price * (1 + self.profit_cut) or price <= self.buy_price * (1 - self.loss_cut):
                self.upbit.sell_market_order(ticker=self.ticker, volume=volume)
                self.sell_price = price
                self.hold = False
                self.record_trade()
                self.send_slack()
                self.buy_price = None
                self.hold_amount = None
                self.sell_price = None

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
        token = "xoxb-2403642842261-2419294353969-YyO0dhtKSLlW8qDhRMyOOKbN"
        if self.hold == True:
            text = self.ticker + ' 구매' + '\n 구매가격' + self.buy_price * (1 + self.fee)
        else:
            text = self.ticker + ' 판매' + '\n 판매가격' + self.buy_price * (1 + self.fee)
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
        coins.append(line)
    f.close()
    coin = []
    for i in range(len(coins)):
        coin.append(Coin(coins[i]))
    while True:
        for i in range(len(coins)):
            print(coins[i])
            # print(coin[i].ticker)
            coin[i].buy_coin()
            coin[i].sell_coin()
            # time.sleep(0.01)
        # print(coin[0].ticker)
        # coin[0].buy_coin()
        # coin[0].sell_coin()
        # print(coin[1].ticker)
        # coin[1].buy_coin()
        # coin[1].sell_coin()
        # print(coin[2].ticker)
        # coin[2].buy_coin()
        # coin[2].sell_coin()
        # print(coin[3].ticker)
        # coin[3].buy_coin()
        # coin[3].sell_coin()
        # print(coin[4].ticker)
        # coin[4].buy_coin()
        # coin[4].sell_coin()
