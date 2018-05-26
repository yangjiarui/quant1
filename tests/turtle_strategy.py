# coding:utf-8
from quant.strategy import Strategy
from quant.main import Quant
from quant.feedbase import CSV
from quant.portfolio import Portfolio
from quant.logging_backtest import logger
import quant.indicator as indicator


class MyStrategy(Strategy):
    def __init__(self, market_event):
        super().__init__(market_event)
        self.market_event = market_event

    def prenext(self):
        pass

    def next(self):
        # ma2 = self.indicator.SMA(period=2, index=-1)
        # high = self.high
        # low = self.low
        # close = self.close
        # # true_range = max(high - low, abs(close.data(1) - high), abs(close.data(1) - low))
        # # average_true_range = talib.SMA(true_range, 20)
        # average_true_range = self.average_true_range.data(5)
        # money = self.balance[-1]
        # units = self.units
        # trade_lots = int(money * 0.01 / (units * average_true_range)) + 1
        # total_trade_lots = 4 * trade_lots
        # max_high = self.max_high.data(5)
        # min_low = self.min_low.data(5)
        # cross = self.cross
        # if cross.crossup(close, max_high):
        #     self.buy(trade_lots)
        # if cross.crossdown(close, min_low):
        #     self.sell(trade_lots)
        high = indicator.Indicators(self.market_event, 'high')
        low = indicator.Indicators(self.market_event, 'low')
        close = indicator.Indicators(self.market_event, 'close')
        close_ref = indicator.Indicators(self.market_event, close, 1)
        logger.info('close_ref and type of it: {} {}'.format(close_ref, type(close_ref)))
        arg1 = high - low
        logger.info('arg1 and type of it: {} {}'.format(arg1, type(arg1)))
        arg2 = indicator.Abs([close_ref - high])
        logger.info('arg2 and type of it: {} {}'.format(arg2, type(arg2)))
        arg3 = indicator.Abs([close_ref - low])
        tr = indicator.Max([arg1, arg2, arg3])
        atr = indicator.MovingAverage([tr, 5])
        money = indicator.Indicators(self.market_event, 'money')
        unit = indicator.Indicators(self.market_event, 'unit')
        tc = indicator.IntPart([money * 0.01 / (unit * atr)])
        mtc = tc * 4  # 4 * tc 不行，__mul__定义问题
        hh = indicator.MaxHigh([high, 5])
        ll = indicator.MinLow([low, 5])







trade = Quant()
data = CSV(
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
