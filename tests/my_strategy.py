# coding:utf-8
from quant.strategy import Strategy
from quant.main import Quant
from quant.feedbase import CSVDataReader, CSV
from quant.portfolio import Portfolio
from quant.logging_backtest import logger
# from quant.indicator import Indicator


class MyStrategy(Strategy):
    def __init__(self, market_event):
        super().__init__(market_event)
        self.first_open = True
        # self.indicator = Indicator(market_event)
        # ma5 = self.indicator.SMA(period=5, index=-1)
        # ma10 = self.indicator.SMA(period=10, index=-1)
        # logger.info('ma5: {}'.format(ma5))
        # logger.info('ma10: {}'.format(ma10))

    def prenext(self):
        # logger.debug('self.bar.open[1]: {}'.format(self.bar.open[1]))
        # logger.debug('self.bar.high[1:]: {}'.format(self.bar.high[1:]))
        # logger.debug('self.bar.low[:2]: {}'.format(self.bar.low[:2]))
        # logger.debug('self.bar.close[:]: {}'.format(self.bar.close[-2:]))
        # logger.debug('self.bar.open[:]: {}'.format(self.bar.open[:]))
        # logger.debug('self.bar.high[:]: {}'.format(self.bar.high[:]))
        # logger.debug('self.bar.low[:]: {}'.format(self.bar.low[:]))
        # logger.debug('self.bar.close[:]: {}'.format(self.bar.close[:]))
        # logger.debug('self.position[-1]: {}'.format(self.position[-1]))
        # logger.debug('self.margin[-1]: {}'.format(self.margin[-1]))
        # logger.debug('self.avg_price[-1]: {}'.format(self.avg_price[-1]))
        # logger.debug('self.unrealized_gain_and_loss[-1]: {}'.format(
        #     self.unrealized_gain_and_loss[-1]))
        # logger.debug('self.realized_gain_and_loss[-1]: {}'.format(
        #     self.realized_gain_and_loss[-1]))
        # logger.debug('self.commission: {}'.format(self.commission))
        logger.debug('self.cash[-1]: {}'.format(self.cash[-1]))
        logger.debug('self.balance[-1]: {}'.format(self.balance[-1]))

    def next(self):
        units = 1
        # ma2 = self.indicator.SMA(period=2, index=-1)
        ma5 = self.indicator.SMA(period=5, index=-1)
        # ma3 = self.indicator.SMA(period=3, index=-1)
        ma10 = self.indicator.SMA(period=10, index=-1)
        logger.info('ma5: {}'.format(ma5))
        logger.info('ma10: {}'.format(ma10))
        # logger.info('MA20: {}'.format(MA20))
        if ma5 > ma10:
            # if self.first_open:  # 如果第一次开仓，则只能买入一次
            #     self.buy(2)
            #     self.first_open = False
            #     return
            self.buy_even_and_open(units)
            # self.buy(2)
            open = self.indicator.open(units)
            logger.info('open in my_strategy: {}'.format(open))
            # self.sell(2)
        elif ma5 < ma10:
            # if self.first_open:  # 如果第一次开仓，则只能卖出一次
            #     self.sell(2)
            #     self.first_open = False
            #     return
            self.sell_even_and_open(units)
            # self.sell(2)
            close = self.indicator.close(units)
            logger.info('close in my_strategy: {}'.format(close))
            # self.buy(2)
        # ma5_last


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
trade.set_commission(commission=0.0003, margin=0.08, mult=300, units=1, instrument='IF')
trade.set_cash(500000)
trade.set_notify()
trade.run()
logger.debug(trade.get_trade_log('IF'))
trade.plot(instrument='IF')
