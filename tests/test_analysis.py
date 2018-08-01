# coding:utf-8
import unittest
import pandas as pd
from quant import analysis
from quant.context import Context
from quant.logging_backtest import logger
from quant.backtestfill import BacktestFill

ohlc_data = pd.read_csv('IF_data.csv', index_col=0)
ohlc_data.index = pd.DatetimeIndex(ohlc_data.index)
context = Context()
context.fill = BacktestFill()
# context.fill.set_dataseries_instrument('IF')
realized_list = [
    {'date': '2013/02/20', 'realized_gain_and_loss': 29880.0},
    {'date': '2013/03/05', 'realized_gain_and_loss': -360.0},
    {'date': '2013/03/08', 'realized_gain_and_loss': -11040.0},
    {'date': '2013/03/12', 'realized_gain_and_loss': -12060.0},
    {'date': '2013/03/22', 'realized_gain_and_loss': -29160.0},
    {'date': '2013/03/29', 'realized_gain_and_loss': -41760.0}]
# for i in realized_list:
#     context.fill.realized_gain_and_loss.add(i['date'], i['realized_gain_and_loss'])

equity = pd.DataFrame()
equity['date'] = [
    '2013-01-07', '2013-01-08', '2013-01-09', '2013-01-10',
    '2013-01-11', '2013-01-14', '2013-01-15', '2013-01-16',
    '2013-01-17', '2013-01-18', '2013-01-21', '2013-01-22',
    '2013-01-23', '2013-01-24', '2013-01-25', '2013-01-28',
    '2013-01-29', '2013-01-30', '2013-01-31', '2013-02-01',
    '2013-02-04', '2013-02-05', '2013-02-06', '2013-02-07',
    '2013-02-08', '2013-02-18', '2013-02-19', '2013-02-20',
    '2013/02/21', '2013/02/22', '2013/02/25', '2013/02/26',
    '2013/02/27', '2013/02/28', '2013/03/01', '2013/03/04',
    '2013/03/05', '2013/03/06', '2013/03/07', '2013/03/08',
    '2013/03/11', '2013/03/12', '2013/03/13', '2013/03/14',
    '2013/03/15', '2013/03/18', '2013/03/19', '2013/03/20',
    '2013/03/21', '2013/03/22', '2013/03/25', '2013/03/26',
    '2013/03/27', '2013/03/28', '2013/03/29',
]
equity.set_index('date', inplace=True)
equity.index = pd.DatetimeIndex(equity.index)
equity['equity'] = [
    500000.00, 500000.00, 500000.00, 500000.00,
    500000.00, 500000.00, 500000.00, 500000.00,
    500000.00, 499705.06, 499045.06, 496705.06,
    498265.06, 492325.06, 487045.06, 500245.06,
    518425.06, 545005.06, 571825.06, 612625.06,
    654325.06, 707665.06, 765265.06, 822265.06,
    874405.06, 917005.06, 946645.06, 529401.12,
    529105.75, 535705.75, 538765.75, 553945.75,
    562225.75, 543265.75, 527845.75, 548005.75,
    528570.31, 528271.99, 518551.99, 517056.95,
    516763.62, 504533.87, 504246.26, 504246.26,
    502926.26, 508386.26, 508146.26, 483846.26,
    457446.26, 474909.94, 474613.91, 459553.91,
    444853.91, 410113.91, 432690.37,
]
trade_log = pd.DataFrame(columns=['date', 'position', 're_profit'])
trade_log['date'] = [
    '2013/01/18', '2013/02/20', '2013/02/21', '2013/03/05',
    '2013/03/06', '2013/03/08', '2013/03/11', '2013/03/12',
    '2013/03/13', '2013/03/22', '2013/03/25', '2013/03/29']
trade_log['position'] = [1, 0, -1, 0, 1, 0, 1, 0, -1, 0, 1, 0]
trade_log['re_profit'] = [0.0, 29880.0, 0.0, -360.0, 0.0, -11040.0,
                          0.0, -12060.0, 0.0, -29160.0, 0.0, -41760.0]
trade_log['equity'] = [
    499705.06, 529401.12, 529105.75, 528570.31, 528271.99, 517056.95,
    516763.62, 504533.87, 504246.26, 474909.94, 474613.91, 432690.37]
context.trade_log = trade_log
capital = 500000


class TestAnalysis(unittest.TestCase):
    def test_get_trade_bars(self):
        op = analysis._true_func
        lenth_bar1 = analysis._get_trade_bars(ohlc_data, trade_log, op)
        self.assertEquals(lenth_bar1, [19, 9, 3, 2, 8, 5])
        logger.info('trade_log: ', trade_log)
        trade_log1 = trade_log.drop([0, 1]).reset_index(drop=True)
        logger.debug('----------------------------------')
        logger.debug('trade_log: ', trade_log1)
        lenth_bar2 = analysis._get_trade_bars(ohlc_data, trade_log1, op)
        self.assertEquals(lenth_bar2, [9, 3, 2, 8, 5])

    def test_duration_of_equity_not_reaching_high(self):
        logger.debug('---equity---: {}'.format(equity))
        date = analysis.duration_of_equity_not_reaching_high(equity)
        logger.debug('---date---: {}'.format(date))
        self.assertEquals(date, '2013/01/07 - 2013/01/28')

    def test_annualized_return_rate(self):
        start = pd.Timestamp(equity.index[0])
        end = pd.Timestamp(equity.index[-1])
        logger.info('---start end---: {} {}'.format(start, end))
        rate = analysis.annualized_return_rate(equity, capital, start, end)
        logger.info('---annualized_return_rate---: {}'.format(rate))
        self.assertEqual(rate, -60.66)

    def test_sharpe_ratio(self):
        rets = equity['equity'].pct_change()
        # sharpe_ratio = analysis.sharpe_ratio(rets)
        sharpe_ratio = analysis.sharpe_ratio(rets, 500000, 28)
        logger.info('---sharpe_ratio---: {}'.format(sharpe_ratio))
        self.assertEqual(sharpe_ratio, 1.0)

    def test_risk_rate(self):
        risk_rate = round(analysis.risk_rate(equity) / 100, 4)
        logger.info('---risk_rate---: {}'.format(risk_rate))
        self.assertEqual(risk_rate, 0.1798)

    def test_profit_rate_in_open(self):
        end_equity = equity['equity'][-1]
        rate = analysis.profit_rate_in_open(end_equity, capital, ohlc_data, trade_log)
        self.assertEqual(rate, -1.07)

    def test_max_consecutive_winning_trades(self):
        number = analysis.max_consecutive_winning_trades(context)
        logger.info('---number---: {}'.format(number))
        self.assertEqual(number, 1)


if __name__ == '__main__':
    unittest.main()
