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

    # def average_true_range(self, period):
    #     """period个周期内的平均真实波幅，一般称为ATR"""
    #     high = self.high()
    #     low = self.low()
    #     last_open = self.open(2)
    #     true_range = max(high - low, high - last_open, last_open - low)
    #     average_true_range = talib.SMA(true_range, period)
    #     return average_true_range

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
        return min(low)

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
    def __init__(self, market_event, period=1):
        super().__init__(market_event)
        self.fill = market_event.fill
        self.period = period

    def data(self):
        # self.period = period
        # return self.period
        return 0.0  # 防止后面定义的add等方法出错

    def data_list(self, period):
        pass

    def __add__(self, other):
        if isinstance(other, Indicators):
            return self.data() + other.data()
        if isinstance(other, int) or isinstance(other, float):
            return self.data() + other

    def __sub__(self, other):
        if isinstance(other, Indicators):
            return self.data() - other.data()
        if isinstance(other, int) or isinstance(other, float):
            return self.data() - other

    def __mul__(self, other):
        if isinstance(other, Indicators):
            return self.data() * other.data()
        if isinstance(other, int) or isinstance(other, float):
            return self.data() * other

    def __truediv__(self, other):
        if isinstance(other, Indicators):
            return self.data() / other.data()
        if isinstance(other, int) or isinstance(other, float):
            return self.data() / other


class Open(Indicators):
    def __init__(self, market_event):
        super().__init__(market_event)

    def data(self):
        open = self.get_basic_data(self.period, ohlc='open')[0]
        return open

    def data_list(self, period=3):
        return self.get_basic_data(period, ohlc='open')


class High(Indicators):
    def __init__(self, market_event):
        super().__init__(market_event)

    def data(self):
        high = self.get_basic_data(self.period, ohlc='high')[0]
        return high

    def data_list(self, period=3):
        return self.get_basic_data(period, ohlc='high')


class Low(Indicators):
    def __init__(self, market_event):
        super().__init__(market_event)

    def data(self):
        low = self.get_basic_data(self.period, ohlc='low')[0]
        return low

    def data_list(self, period=3):
        return self.get_basic_data(period, ohlc='low')


class Close(Indicators):
    def __init__(self, market_event):
        super().__init__(market_event)

    def data(self):
        close = self.get_basic_data(self.period, ohlc='close')[0]
        return close

    def data_list(self, period=3):
        return self.get_basic_data(period, ohlc='close')


class MaxHigh(Indicators):
    def __init__(self, market_event):
        super().__init__(market_event)

    def data(self):
        high = self.get_basic_data(self.period, ohlc='high')
        return max(high)

    def data_list(self, period):
        max_high_list = []
        # 最近三个period周期内的最高价
        for i in range(3):
            if i == 0:
                max_high_data = max(self.get_basic_data(period))
            else:
                max_high_data = max(self.get_basic_data(period + i)[:-i])
            max_high_list.append(max_high_data)
        return max_high_list


class MinLow(Indicators):
    def __init__(self, market_event):
        super().__init__(market_event)

    def data(self):
        low = self.get_basic_data(self.period, ohlc='low')
        return max(low)

    def data_list(self, period):
        min_low_list = []
        # 最近三个period周期内的最高价
        for i in range(3):
            if i == 0:
                min_low_data = max(self.get_basic_data(period))
            else:
                min_low_data = max(self.get_basic_data(period + i)[:-i])
            min_low_list.append(min_low_data)
        return min_low_list


class Cross(Indicators):
    def __init__(self, market_event):
        super().__init__(market_event)

    def crossup(self, arg1, arg2):
        if isinstance(arg1, Indicators) and isinstance(arg2, Indicators):
            arg1_list = arg1.data_list()
            arg2_list = arg2.data_list()
            if arg1_list[-1] > arg2_list[-1]:
                if arg1_list[-2] == arg2_list[-2]:
                    if arg1_list[-3] < arg2_list[-3]:
                        return True
                if arg1_list[-2] < arg2_list[-2]:
                    return True
            else:
                return False
        else:
            return False

    def crossdown(self, arg1, arg2):
        if isinstance(arg1, Indicators) and isinstance(arg2, Indicators):
            arg1_list = arg1.data_list()
            arg2_list = arg2.data_list()
            if arg1_list[-1] < arg2_list[-1]:
                if arg1_list[-2] == arg2_list[-2]:
                    if arg1_list[-3] > arg2_list[-3]:
                        return True
                if arg1_list[-2] > arg2_list[-2]:
                    return True
            else:
                return False
        else:
            return False


class AverageTrueRange(Indicators):
    def __init__(self, market_event, period):
        super().__init__(market_event)
        self.period = period
        self.high = High(market_event)
        self.low = Low(market_event)
        self.close = Close(market_event)

    def data(self):
        for i in range(self.period):
            arg1 = self.high.data_list(self.period)  # period周期内的最高价
            arg2 = self.low.data_list(self.period)  # period周期内的最低价
            arg3 = self.close.data_list(self.period)  # period周期内的收盘价
            true_range = arg1