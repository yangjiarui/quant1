# coding:utf-8
from quant.strategy import StrategyBase
from quant.main import Quant
from quant.feedbase import CSVDataReader
from quant.portfolio import Portfolio
from quant.logging_backtest import logger


class MyStrategy(StrategyBase):
    def __init__(self, market_event):
        super().__init__(market_event)

    def prenext(self):
        logger.info('self.bar.open[1]: {}'.format(self.bar.open[1]))
        logger.info('self.bar.high[1:]: {}'.format(self.bar.high[1:]))
        logger.info('self.bar.low[:2]: {}'.format(self.bar.low[:2]))
        logger.info('self.bar.close[-2:]: {}'.format(self.bar.close[-2:]))
        logger.info('self.position[-1]: {}'.format(self.position[-1]))
        logger.info('self.margin[-1]: {}'.format(self.margin[-1]))
        logger.info('self.avg_price[-1]: {}'.format(self.avg_price[-1]))
        logger.info('self.unrealized_gain_and_loss[-1]: {}'.format(
            self.unrealized_gain_and_loss[-1]))
        logger.info('self.realized_gain_and_loss[-1]: {}'.format(
            self.realized_gain_and_loss[-1]))
        logger.info('self.commission: {}'.format(self.commission))
        logger.info('self.cash[-1]: {}'.format(self.cash[-1]))
        logger.info('self.balance[-1]: {}'.format(self.balance[-1]))

    def next(self):
        if self.indicator.SMA(
                period=5, index=-1) > self.indicator.SMA(
                    period=10, index=-1):
            self.buy(2)
        else:
            self.sell(2)


trade = Quant()
data = CSVDataReader(
    # datapath='../data/IF_cleaned_data.csv',
    datapath='/home/demlution/桌面/quant/data/IF_cleaned_data.csv',
    instrument='IF',
    startdate='2015-04-03',
    enddate='2015-04-10')
data_list = [data]
portfolio = Portfolio
strategy = MyStrategy

trade.set_backtest(data_list, [strategy], portfolio)
trade.set_commission(commission=0.0003, margin=0.15, mult=10, instrument='IF')
trade.set_cash(500000)
trade.set_notify()
trade.run()
logger.info(trade.get_trade_log('IF'))
trade.plot(instrument='IF')

