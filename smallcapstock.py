#!/usr/bin/python2
#coding: utf-8 

from __future__ import division

from selector import select
from trader import trader
from download import download
from common import get_stock_prefix

SRC = 'http://qt.gtimg.cn/q=%s'

class smallCapStock:
    def __init__(self, target_num=10):
        ''' 当日全部股票 '''
        self.stocks_info = select(read_cache=False)
        self.target_num = target_num
        self.trader = trader()

    def min_volume_stocks(self):
        sort_stocks = sorted(self.stocks_info.values(), key=lambda x: float(x['market_value']))
        target_stocks = sort_stocks[:self.target_num]
        return {i['code']:i for i in target_stocks}, sort_stocks[self.target_num]

    def suspend(self, stocks):
        urls = []
        for i in stocks:
            url = SRC % (get_stock_prefix(str(i)) + str(i))
            html = download().get(url)
            volume = html.split('~')[6]
            if int(volume)== 0:
                urls.append(str(i))
        return urls

    def adjust(self):
        # 10支最小市值股票 
        target_stocks_info, target_add_stock = self.min_volume_stocks()
        # 持仓股票
        holding_stocks = self.trader.holding.keys()
        # 持仓停牌股票
        suspend_stocks = self.suspend(holding_stocks)
        # 目标股票
        m = target_stocks_info.keys() 
        target_stocks = m if len(suspend_stocks) == 0 else m[:len(m)-len(suspend_stocks)] + suspend_stocks

        # 清仓 
        clear_stocks = [i for i in holding_stocks if i not in target_stocks]
        if len(holding_stocks) == 1 and len(clear_stocks) != 0:
            self.sell_out(clear_stocks, weight = 1)
        elif len(holding_stocks) == len(clear_stocks):
            self.sell_out(clear_stocks, weight = -1)
        else:
            self.sell_out(clear_stocks)
        # 开仓
        self.buy_in([i for i in target_stocks if i not in holding_stocks])

        # 剩余余额买target_num+1标的
        self.buy_in([target_add_stock.get('code')], first=False)

    def sell_out(self, stocks, weight=0):
        ''' 清仓
        '''
        for num, stock in enumerate(stocks):
            if stock == '000803':
                continue
            d_weight =  0 if weight == -1 else weight
            if weight == -1 and num == len(stocks)-1:
                d_weight = 1
            if d_weight <= 100 and d_weight >= 0:
                self.trader.sell(stock, d_weight)

    def buy_in(self, stocks, first=True):
        ''' 开仓 
            first 针对剩余金额全部购买一支标的进行处理
        '''
        # 重新获取交易信息
        self.trader = trader()
        # 账户可用余额(百分比)
        enable_balance = 100 - sum([i['weight'] for i in self.trader.holding.values()])
        for stock in stocks:
            weight = (enable_balance/len(stocks)) if first else enable_balance
            if weight <=100 and weight>=0:
                self.trader.buy(stock, int(weight))

if __name__ == '__main__':
    scs = smallCapStock()
    scs.adjust()
