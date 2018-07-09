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
        # money = self.equity[-1]
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

        """后续再考虑变量的问题，先把策略写死，往后进行"""
        # high = indicator.Indicators(self.market_event, 'high')
        # logger.info('high.data_dict: {}'.format(high.data_dict))
        # low = indicator.Indicators(self.market_event, 'low')
        # close = indicator.Indicators(self.market_event, 'close')
        # close_ref = indicator.Indicators(self.market_event, close, 1)
        # logger.info('close_ref and type of it: {} {}'.format(close_ref, type(close_ref)))
        # arg1 = high - low
        # value = indicator.Evaluate(arg1)
        # value = value.evaluate()
        # logger.info('value: {}'.format(value))
        # logger.info('arg1 and type of it: {} {}'.format(arg1, type(arg1)))
        # logger.info('arg1.data_dict: {}'.format(arg1.data_dict))
        # arg2 = abs(close_ref - high)
        # logger.info('arg2 and type of it: {} {}'.format(arg2, type(arg2)))
        # arg3 = abs(close_ref - low)
        # tr = indicator.Indicators.max(arg1, arg2, arg3)
        # logger.info('tr.data_dict: {}'.format(tr.data_dict))
        # atr = indicator.Indicators.moving_average(tr, 5)
        # logger.info('self.equity: {}'.format(self.equity))
        # logger.info('self.equity[-1]: {}'.format(self.equity[-1]))
        # money = self.equity[-1]
        # logger.info('money: {}'.format(money))
        # unit = self.units
        # tc = indicator.Indicators.int_part(money * 0.01 / unit * atr)
        # mtc = tc * 4
        # hh = indicator.Indicators.max_high(high, 5)
        # ll = indicator.Indicators.min_low(low, 5)

        #  引用技术指标基类，方便调用各种参数
        indi = indicator.Indicator(self.market_event)
        money = indi.money()
        unit = indi.units()
        atr = indi.average_true_range(4)
        tc = int(money * 0.01 / (unit * atr))
        mtc = 4 * tc
        # 列表中放入数据时，前面周期的数据放前面，当前周期的数据放后面
        close = []
        close.append(indi.close(2)[0])  # 前一周期的 close
        close.append(indi.close(1)[0])  # 当前周期的 close
        logger.info('close list: {}'.format(close))
        max_high = []
        max_high.append(indi.max_high(3, 1))
        max_high.append(indi.max_high(3))
        min_low = []
        min_low.append(indi.min_low(3, 1))
        min_low.append(indi.min_low(3))
        up = indi.cross_up(close, max_high)
        logger.info('up上穿: {}'.format(up))
        down = indi.cross_down(close, max_high)
        logger.info('down下穿: {}'.format(down))








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
