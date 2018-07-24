# coding:utf-8
import unittest
import pandas as pd
from quant import analysis


class TestAnalysis(unittest.TestCase):
    def test_get_trade_bars(self):
        op = analysis._true_func
        ohlc_data = pd.read_csv('IF_data.csv', index_col=0)
        ohlc_data.index = pd.DatetimeIndex(ohlc_data.index)
        trade_log = pd.DataFrame(columns=['date', 'position', 're_profit'])
        trade_log['date'] = [
            '2013/01/18', '2013/02/20', '2013/02/21', '2013/03/05',
            '2013/03/06', '2013/03/08', '2013/03/11', '2013/03/12',
            '2013/03/13', '2013/03/22', '2013/03/25', '2013/03/29']
        trade_log['position'] = [1, 0, -1, 0, 1, 0, 1, 0, -1, 0, 1, 0]
        trade_log['re_profit'] = list(range(12))
        lenth_bar1 = analysis._get_trade_bars(ohlc_data, trade_log, op)
        self.assertEquals(lenth_bar1, [19, 9, 3, 2, 8, 5])
        trade_log.drop([0, 1])
        lenth_bar2 = analysis._get_trade_bars(ohlc_data, trade_log, op)
        self.assertEquals(lenth_bar2, [9, 3, 2, 8, 5])


if __name__ == '__main__':
    unittest.main()
