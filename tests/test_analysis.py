# coding:utf-8
import unittest
import pandas as pd
from quant import analysis
from quant.context import Context
from quant.logging_backtest import logger

ohlc_data = pd.read_csv('IF_data.csv', index_col=0)
ohlc_data.index = pd.DatetimeIndex(ohlc_data.index)
context = Context()
# context.fill.realized_gain_and_loss

equity = pd.DataFrame()
equity['date'] = [
    '2013-01-07', '2013-01-08', '2013-01-09', '2013-01-10',
    '2013-01-11', '2013-01-14', '2013-01-15', '2013-01-16',
    '2013-01-17', '2013-01-18', '2013-01-21', '2013-01-22',
    '2013-01-23', '2013-01-24', '2013-01-25', '2013-01-28',
    '2013-01-29', '2013-01-30', '2013-01-31', '2013-02-01',
    '2013-02-04', '2013-02-05', '2013-02-06', '2013-02-07',
    '2013-02-08', '2013-02-18', '2013-02-19', '2013-02-20',
]
equity.set_index('date', inplace=True)
equity.index = pd.DatetimeIndex(equity.index)
equity['equity'] = [
    500000.00, 500000.00, 500000.00, 500000.00,
    500000.00, 500000.00, 500000.00, 500000.00,
    500000.00, 499765.06, 499105.06, 496765.06,
    498325.06, 492385.06, 487105.06, 500305.06,
    518485.06, 545065.06, 571885.06, 612685.06,
    654385.06, 707725.06, 765325.06, 822325.06,
    874465.06, 917065.06, 946705.06, 529521.12,
]


class TestAnalysis(unittest.TestCase):
    def test_get_trade_bars(self):
        op = analysis._true_func
        trade_log = pd.DataFrame(columns=['date', 'position', 're_profit'])
        trade_log['date'] = [
            '2013/01/18', '2013/02/20', '2013/02/21', '2013/03/05',
            '2013/03/06', '2013/03/08', '2013/03/11', '2013/03/12',
            '2013/03/13', '2013/03/22', '2013/03/25', '2013/03/29']
        trade_log['position'] = [1, 0, -1, 0, 1, 0, 1, 0, -1, 0, 1, 0]
        trade_log['re_profit'] = list(range(12))
        lenth_bar1 = analysis._get_trade_bars(ohlc_data, trade_log, op)
        self.assertEquals(lenth_bar1, [19, 9, 3, 2, 8, 5])
        logger.debug('trade_log: ', trade_log)
        trade_log = trade_log.drop([0, 1]).reset_index(drop=True)
        logger.debug('----------------------------------')
        logger.debug('trade_log: ', trade_log)
        lenth_bar2 = analysis._get_trade_bars(ohlc_data, trade_log, op)
        self.assertEquals(lenth_bar2, [9, 3, 2, 8, 5])

    def test_duration_of_equity_not_reaching_high(self):
        logger.debug('---equity---: {}'.format(equity))
        date = analysis.duration_of_equity_not_reaching_high(equity)
        logger.debug('---date---: {}'.format(date))
        self.assertEquals(date, '2013/01/07 - 2013/01/28')

    def test_annualized_return_rate(self):
        start = pd.Timestamp('2013-01-07')
        end = pd.Timestamp('2013-02-20')
        capital = 500000
        rate = analysis.annualized_return_rate(equity, capital, start, end)
        logger.info('---annualized_return_rate---: {}'.format(rate))
        self.assertEquals(rate, 48.98)

    def test_sharpe_ratio(self):
        rets = equity['equity'].pct_change()
        sharpe_ratio = analysis.sharpe_ratio(rets)
        logger.info('---sharpe_ratio---: {}'.format(sharpe_ratio))
        self.assertEquals(sharpe_ratio, 1.0)


if __name__ == '__main__':
    unittest.main()
