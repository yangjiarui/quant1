# coding:utf-8
from quant.strategy import Strategy
from quant.main import Quant
from quant.feedbase import CSVDataReader
from quant.portfolio import Portfolio
from quant.logging_backtest import logger
import talib


class MyStrategy(Strategy):
    def __init__(self, market_event):
        super().__init__(market_event)

    def prenext(self):
        pass

    def next(self):
        # ma2 = self.indicator.SMA(period=2, index=-1)
        high = self.high
        low = self.low
        close = self.close
        true_range = max(high - low, abs(close.data(1) - high), abs(close.data(1) - low))
        average_true_range = talib.SMA(true_range, 20)
        money = self.indicator.money()
        units = self.units
        trade_lots = int(money * 0.01 / (units * average_true_range))
        total_trade_lots = 4 * trade_lots
        max_high = self.max_high(20)
        min_low = self.min_low(20)
        cross = self.cross





trade = Quant()
data = CSVDataReader(
    # datapath='../data/IF_cleaned_data.csv',
    datapath='../data/CFFEX沪深300期货IF主连.csv',
    # datapath='/home/demlution/桌面/quant/data/IF_cleaned_data.csv',
    instrument='IF',
    startdate='2013-01-04',
    enddate='2017-12-11')
data_list = [data]
portfolio = Portfolio
strategy = MyStrategy

trade.set_backtest(data_list, [strategy], portfolio)
trade.set_commission(commission=0.0003, margin=0.15, units=300, lots=2, instrument='IF')
trade.set_cash(500000)
trade.set_notify()
trade.run()
logger.debug(trade.get_trade_log('IF'))
# trade.plot(instrument='IF')
