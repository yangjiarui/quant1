# coding:utf-8
from quant.strategy import Strategy
from quant.main import Quant
from quant.feedbase import CSVDataReader
from quant.portfolio import Portfolio
from quant.logging_backtest import logger


class MyStrategy(Strategy):
    def __init__(self, market_event):
        super().__init__(market_event)
        self.first_open = True

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
        ma2 = self.indicator.SMA(period=2, index=-1)
        # MA5 = self.indicator.SMA(period=5, index=-1)
        ma3 = self.indicator.SMA(period=3, index=-1)
        # MA10 = self.indicator.SMA(period=10, index=-1)
        # MA20 = self.indicator.SMA(period=20, index=-1)
        logger.info('MA2: {}'.format(ma2))
        logger.info('MA3: {}'.format(ma3))
        # logger.info('MA10: {}'.format(MA10))
        # logger.info('MA20: {}'.format(MA20))
        if ma2 > ma3:
            if self.first_open:  # 如果第一次开仓，则只能买入一次
                self.buy(2)
                self.first_open = False
                return
            self.buy_even_and_open(2)
            # self.buy(2)
        elif ma2 < ma3:
            if self.first_open:  # 如果第一次开仓，则只能卖出一次
                self.sell(2)
                self.first_open = False
                return
            self.sell_even_and_open(2)
            # self.sell(2)


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
