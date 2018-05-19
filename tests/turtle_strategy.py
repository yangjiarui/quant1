# coding:utf-8
from quant.strategy import Strategy
from quant.main import Quant
from quant.feedbase import CSVDataReader
from quant.portfolio import Portfolio
from quant.logging_backtest import logger


class MyStrategy(Strategy):
    def __init__(self, market_event):
        super().__init__(market_event)

    def prenext(self):
        pass

    def next(self):
        ma2 = self.indicator.SMA(period=2, index=-1)



trade = Quant()
data = CSVDataReader(
    datapath='../data/IF_cleaned_data.csv',
    # datapath='/home/demlution/桌面/quant/data/IF_cleaned_data.csv',
    instrument='IF',
    startdate='2015-04-06',
    enddate='2015-04-10')
data_list = [data]
portfolio = Portfolio
strategy = MyStrategy

trade.set_backtest(data_list, [strategy], portfolio)
trade.set_commission(commission=0.0003, margin=0.15, mult=300, units=2, instrument='IF')
trade.set_cash(500000)
trade.set_notify()
trade.run()
logger.debug(trade.get_trade_log('IF'))
# trade.plot(instrument='IF')
