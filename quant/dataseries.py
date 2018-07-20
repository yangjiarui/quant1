# coding:utf-8
import numpy as np
import pandas as pd
from quant.logging_backtest import logger


class DataSeriesBase(object):
    _name = None  # 后面必须先设置名字
    _instrument = None

    def __init__(self):
        self._dict = {}
        self.old_date = None

    def __getitem__(self, key):
        # print('self._instrument: {}'.format(self._instrument))
        # print(key)
        # print(self._name)
        # logger.debug(
        #     'self._dict[self._instrument][key][self._name]: {}'.format(
        #         self._dict[self._instrument][key][self._name]))
        return self._dict[self._instrument][key][self._name]

    def initialize(self, instrument, initial):
        self._dict[instrument] = [{'date': 'start', self._name: initial}]

    def set_instrument(self, instrument):
        self._instrument = instrument

    def add(self, date, value):
        logger.debug('self.old_date, date in add dataseries: {} {}'.format(self.old_date, date))
        if self.old_date != date:
            if self._dict[self._instrument][0]['date'] == 'start':
                self._dict[self._instrument] = []
            self._dict[self._instrument].append({'date': date, self._name: value})
            # logger.debug('self._dict in dataseries: {}'.format(self._dict))
            self.old_date = date
        else:
            logger.debug('self.old_date, date in add dataseries: {} {}'.format(self.old_date, date))
            logger.debug('date in dataseries.add: {}'.format(date))
            logger.debug('value in add: {}'.format(value))
            self._dict[self._instrument][-1][self._name] = value

    @property
    def dict(self):
        return self._dict[self._instrument]

    @property
    def keys(self):
        return self._dict.keys()

    @property
    def date(self):
        return [i['date'] for i in self._dict[self._instrument]]

    @property
    def list(self):
        return [i[self._name] for i in self._dict[self._instrument]]

    @property
    def df(self):  # 转换数据为DataFrame格式
        df = pd.DataFrame(self._dict[self._instrument][:])  # 从 1 开始会少一个数
        df.set_index('date', inplace=True)
        df.index = pd.DatetimeIndex(df.index)
        return df

    @property
    def series(self):
        return self.df[self._name]

    @property
    def array(self):
        return np.array(self.list)

    @property
    def total_dict(self):
        return self._dict

    def plot(self):
        self.df.plot()

    def del_last(self):  # 此处待测试
        self._dict[self._instrument].pop(-2)

    def copy_last(self, new_date):  # 更新日期
        logger.debug('new_date in dataseries copy_last: {}'.format(new_date))
        self._dict[self._instrument].append(self._dict[self._instrument][-1])
        self._dict[self._instrument][-1]['date'] = new_date

    def total(self, key=-1, name=None):
        """全部instrument合起来的value"""
        if name is None:
            name = self._name
        value = 0
        for i in self._dict.values():  # 多个self._instrument列表
            value += i[key][name]
        return value


class PositionSeries(DataSeriesBase):
    """仓位"""
    _name = 'position'


class MarginSeries(DataSeriesBase):
    """保证金"""
    _name = 'margin'


class AvgPriceSeries(DataSeriesBase):
    """均价"""
    _name = 'avg_price'


class CommissionSeries(DataSeriesBase):
    """手续费"""
    _name = 'commission'


class LongCommissionSeries(DataSeriesBase):
    """多头手续费"""
    _name = 'long_commission'


class ShortCommissionSeries(DataSeriesBase):
    """空头手续费"""
    _name = 'short_commission'


class CashSeries(DataSeriesBase):
    """现金"""
    _name = 'cash'
    _instrument = 'all'


class RealizedGainAndLossSeries(DataSeriesBase):
    """平仓盈亏，即已获得的盈亏"""
    _name = 'realized_gain_and_loss'
    re_profit = []  # 总平仓盈亏
    long_poisition_re_profit = []  # 多头平仓盈亏
    short_position_re_profit = []  # 空头平仓盈亏
    # def update_cur(self, realized_gain_and_loss):
    #     self._dict[self._instrument][-1][
    #         'realized_gain_and_loss'] = realized_gain_and_loss


class LongRealizedGainAndLossSeries(DataSeriesBase):
    """多头盈亏，含手续费"""
    _name = 'long_realized_gain_and_loss'


class ShortRealizedGainAndLossSeries(DataSeriesBase):
    """空头盈亏，含手续费"""
    _name = 'short_realized_gain_and_loss'


class UnrealizedGainAndLossSeries(DataSeriesBase):
    """浮动盈亏，即账面盈亏，还未获得，需平仓才能获得"""
    _name = 'unrealized_gain_and_loss'

    # def initialize(self, instrument, initial):
    #     self._dict[instrument] = [{
    #         'date': 'start',
    #         self._name: initial,
    #         # 'unrealized_gain_and_loss_high': initial,
    #         # 'unrealized_gain_and_loss_low': initial,
    #     }]
    #
    # def add(self, date, unrealized_gain_and_loss):
    #     self._dict[self._instrument].append({
    #         'date': date,
    #         self._name: unrealized_gain_and_loss,
    #     })

    # def add(self, date, unrealized_gain_and_loss,
    #         unrealized_gain_and_loss_high, unrealized_gain_and_loss_low):
    #     self._dict[self._instrument].append({
    #         'date': date,
    #         self._name: unrealized_gain_and_loss,
    #         'unrealized_gain_and_loss_high': unrealized_gain_and_loss_high,
    #         'unrealized_gain_and_loss_low': unrealized_gain_and_loss_low,
    #     })

    # @property
    # def high(self):
    #     return [i['unrealized_gain_and_loss_high'] for i in self._dict[self._instrument]]

    # @property
    # def low(self):
    #     return [i['unrealized_gain_and_loss_low'] for i in self._dict[self._instrument]]

    # def total_high(self, key=-1):
    #     return self.total(key, 'unrealized_gain_and_loss_high')

    # def total_low(self, key=-1):
    #     return self.total(key, 'unrealized_gain_and_loss_low')


class EquitySeries(DataSeriesBase):
    """余额"""
    _name = 'equity'
    _instrument = 'all'

    # def initialize(self, instrument, initial):
    #     self._dict[self._instrument] = [{
    #         'date': 'start',
    #         self._name: initial,
    #     }]
    #
    # def add(self, date, equity):
    #     self._dict[self._instrument].append({
    #         'date': date,
    #         self._name: equity,
    #     })

    # def initialize(self, instrument, initial):
    #     self._dict[self._instrument] = [{
    #         'date': 'start',
    #         self._name: initial,
    #         'equity_high': initial,
    #         'equity_low': initial,
    #     }]

    # def add(self, date, equity, equity_high, equity_low):
    #     self._dict[self._instrument].append({
    #         'date': date,
    #         self._name: equity,
    #         'equity_high': equity_high,
    #         'equity_low': equity_low,
    #     })

    # @property
    # def high(self):
    #     return [i['equity_high'] for i in self._dict[self._instrument]]

    # @property
    # def low(self):
    #     return [i['equity_low'] for i in self._dict[self._instrument]]
