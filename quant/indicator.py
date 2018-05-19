# coding:utf-8
import talib
import numpy as np
from copy import copy


class IndicatorBase(object):
    """指标基类"""

    def __init__(self, market_event):
        self.preload_bar_list = []
        self.instrument = market_event.instrument
        self.iteration_buffer = market_event.feed.iteration_buffer
        # 备份bar中的数据，格式为[{'date', 'open', 'high', 'low', 'close'}, {}, ...]
        self.bar_list = copy(market_event.bar.data)
        self.bar_list2 = copy(self.bar_list)
        self.preload_bar_list = market_event.feed.preload_bar_list

    def get_preload(self, period, index, ohlc='close'):
        """
        将preload插入到bar_dict前，然后根据当前时间点动态
        获取固定长度(|-period+index|)的数据
        """
        preload = self.preload_bar_list[:period]
        self.bar_list = copy(self.bar_list2)
        for i in preload:
            self.bar_list.insert(0, i)

        data = [i[ohlc] for i in self.bar_list][-period + index:]
        return np.array(data)

    def get_basic_data(self, period, ohlc='close'):
        """获取基础的数据，如open, high, low, close等，最后取得一个列表，长度为period"""
        data_list = self.bar_list[-period:]
        data = [i[ohlc] for i in data_list]
        return np.array(data)


class Indicator(IndicatorBase):
    """自定义指标，如简单移动平均指标"""

    def __init__(self, market_event):
        super().__init__(market_event)
        self.SMA = self.simple_moving_average
        self.fill = market_event.fill

    def simple_moving_average(self, period, index=-1):
        close = self.get_preload(period, index, 'close')
        sma_close = talib.SMA(close, period)  # 返回array，period个数前计算会得到nan，需处理
        if np.isnan(sma_close[index]):
            raise Warning
        else:
            return sma_close[index]

    def open(self, period=1):
        open = self.get_basic_data(period, ohlc='open')[0]
        return open

    def high(self, period=1):
        high = self.get_basic_data(period, ohlc='high')[0]
        return high

    def low(self, period=1):
        low = self.get_basic_data(period, ohlc='low')[0]
        return low

    def close(self, period=1):
        close = self.get_basic_data(period, ohlc='close')[0]
        return close

    def average_true_range(self, period):
        """period个周期内的平均真实波幅，一般称为ATR"""
        high = self.high()
        low = self.low()
        last_open = self.open(2)
        true_range = max(high - low, high - last_open, last_open - low)
        average_true_range = talib.SMA(true_range, period)
        return average_true_range

    def money(self):
        return self.fill.balance[-1]['balance']

    def units(self):
        return self.fill.units

    def position(self):
        return self.fill.position[-1]['position']

    def max_high(self, period):
        """获取period个周期内的最高价"""
        high = self.get_basic_data(period, ohlc='high')
        return max(high)

    def min_low(self, period):
        """获取period个周期内的最低价"""
        low = self.get_basic_data(period, ohlc='low')
        return max(low)

    def is_last_bk(self):
        """是否已买入开仓"""
        position = self.position()
        if position > 0:
            return 1
        else:
            return 0

    def is_last_sk(self):
        """是否已卖出开仓"""
        position = self.position()
        if position < 0:
            return 1
        else:
            return 0


class Indicators(IndicatorBase):
    """
    自定义open
    example:
    class A(object):
        def data(self):
            return 1

        def __add__(self, other):
            if isinstance(other, object):
                return self.data() + other.data()


    class B(object):
        def data(self):
            return 2

        def __add__(self, other):
            if isinstance(other, object):
                return self.data() + other.data()


    aa = A()
    bb = B()
    print(aa + bb)  # 1 + 2 = 3, 只能做一次加法，多次加法会出错，如aa + bb + aa
    """
    def __init__(self, market_event):
        super().__init__(market_event)
        self.fill = market_event.fill

    def data(self, period):
        self.period = period

    def __add__(self, other):
        if isinstance(other, IndicatorBase):
            return self.data(self.period) + other.data(self.period)

    def __sub__(self, other):
        if isinstance(other, IndicatorBase):
            return self.data(self.period) - other.data(self.period)

    def __mul__(self, other):
        if isinstance(other, IndicatorBase):
            return self.data(self.period) * other.data(self.period)

    def __truediv__(self, other):
        if isinstance(other, IndicatorBase):
            return self.data(self.period) / other.data(self.period)


class open(Indicators):
    def __init__(self, market_event):
        super().__init__(market_event)

    def data(self, period):
        open = self.get_basic_data(period, ohlc='open')[0]
        return open


class High(Indicators):
    def __init__(self, market_event):
        super().__init__(market_event)

    def data(self, period):
        high = self.get_basic_data(period, ohlc='high')[0]
        return high


class Low(Indicators):
    def __init__(self, market_event):
        super().__init__(market_event)

    def data(self, period):
        low = self.get_basic_data(period, ohlc='low')[0]
        return low


class Close(Indicators):
    def __init__(self, market_event):
        super().__init__(market_event)

    def data(self, period):
        close = self.get_basic_data(period, ohlc='close')[0]
        return close
