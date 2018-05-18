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


class Indicator(IndicatorBase):
    """自定义指标，如简单移动平均指标"""

    def __init__(self, market_event):
        super().__init__(market_event)
        self.SMA = self.simple_moving_average
        self.num1 = 0
        self.num2 = 0

    def simple_moving_average(self, period, index=-1):
        close = self.get_preload(period, index, 'close')
        sma_close = talib.SMA(close, period)  # 返回array，period个数前计算会得到nan，需处理
        if np.isnan(sma_close[index]):
            raise Warning
        else:
            return sma_close[index]

    def open(self, period=1):
        open = self.get_preload(period, index=-1, ohlc='open')
        return open

    def high(self, period=1):
        high = self.get_preload(period, index=-1, ohlc='high')
        return high

    def low(self, period=1):
        low = self.get_preload(period, index=-1, ohlc='low')
        return low

    def close(self, period=1):
        close = self.get_preload(period, index=-1, ohlc='close')
        return close

    def crossup(self, num1, num2):
        num_a = num1
        num_b = num2

