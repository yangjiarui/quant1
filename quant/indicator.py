# coding:utf-8
import talib
import numpy as np
from copy import copy, deepcopy
from quant.logging_backtest import logger
from collections import deque


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

    # def money(self):
    #     return self.fill.balance[-1]['balance']

    # def units(self):
    #     return self.fill.units

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


class DataInClassDict(dict):
    """
    用于储存表达式的字典
    d = DataInClassDict()
    d['a']['b']
    d['a']['c']
    d['c']['d']
    >>>{'a': {'b': {}, 'c': {}}, 'c': {'d': {}}}
    """
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value


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
    def __init__(self, market_event, field=None, period=1):
        super().__init__(market_event)
        self.market_event = market_event
        self.fill = market_event.fill
        self.field = field
        self.period = period
        self.data_dict = DataInClassDict()
        self.data_dict['arg'] = []
        self.data_dict['func'] = None

    def get_real_data(self):
        if self.field is 'money':
            data = self.fill.balance[-1]['balance']
        elif self.field is 'unit':
            data = self.field.units
        else:
            data = self.get_basic_data(self.period, ohlc=self.field)[0]
        return data

    def get_real_data_list(self):
        if self.field in ['money', 'unit']:
            return
        else:
            data_list = self.get_basic_data(self.period, ohlc=self.field)
            return data_list

    def moving_average(self, period):
        # 保存当前的和前一日期的简单移动平均值
        # ma_list = []
        # ma_list.append(self.get_basic_data(self.period + 1, self.field)[:-1])
        # ma_list.append(self.get_basic_data(self.period, self.field))
        # return ma_list
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'moving_average'
        another.data_dict['arg'] += [period]
        return another

    def __add__(self, other):
        """类 + other, 类指的是Indicators, 下同"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = '+'
        another.data_dict['arg'].append(other)
        return another

    def __sub__(self, other):
        """类 - other"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = '-'
        another.data_dict['arg'].append(other)
        return another

    def __mul__(self, other):
        """类 × other"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = '*'
        another.data_dict['arg'].append(other)
        return another

    def __truediv__(self, other):
        """类 / other"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = '/'
        another.data_dict['arg'].append(other)
        return another

    def __radd__(self, other):
        """other + 类"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(other)
        another.data_dict['func'] = '+'
        another.data_dict['arg'].append(self)
        return another

    def __rsub__(self, other):
        """other - 类"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(other)
        another.data_dict['func'] = '-'
        another.data_dict['arg'].append(self)
        return another

    def __rmul__(self, other):
        """other × 类"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(other)
        another.data_dict['func'] = '*'
        another.data_dict['arg'].append(self)
        return another

    def __rtruediv__(self, other):
        """other / 类"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(other)
        another.data_dict['func'] = '/'
        another.data_dict['arg'].append(self)
        return another

    def __abs__(self):
        """abs(类)"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'abs'
        return another

    def max(self, *args):
        """Indicators.max(类, *args)"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'max'
        another.data_dict['arg'] += [*args]
        return another

    def min(self, *args):
        """Indicators.min(类, *args)"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'min'
        another.data_dict['arg'] += [*args]
        return another

    def int_part(self):
        """Indicators.int_part(类)"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'int'
        return another

    def max_high(self, *args):
        """Indicators.max_high(类, *args)"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'max_high'
        another.data_dict['arg'] += [*args]
        return another

    def min_low(self, *args):
        """Indicators.min_low(类, *args)"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'min_low'
        another.data_dict['arg'] += [*args]
        return another

    def cross_up(self, *args):
        """Indicators.cross_up(类, *args)"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'cross_up'
        another.data_dict['arg'] += [*args]
        return another

    def cross_down(self, *args):
        """Indicators.cross_down(类, *args)"""
        another = Indicators(self.market_event)
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'cross_down'
        another.data_dict['arg'] += [*args]
        return another


class Evaluate(object):
    """判断买入卖出时机时，进行解析"""
    def __init__(self, unevaluated: Indicators):
        self.func_list = []
        self.unevaluated = copy(unevaluated)
        self.data = []  # 暂时存储计算数据

    def get_func(self):
        for key, value in self.unevaluated.data_dict.items():
            if value is 'func':
                self.func_list.append(value)

    def evaluate(self):
        while True:
            value = 'None'
            if len(self.unevaluated.data_dict['func']):
                self.func_list.append(self.unevaluated.data_dict['func'])
                del self.unevaluated.data_dict['func']
            else:
                for i in self.unevaluated.data_dict['arg']:
                    self.data.append(i.get_real_data())
            if self.func_list[0] in ['+', '-', '*', '/']:
                if self.data:
                    data_str = [str(i) for i in self.data]
                    value = self.func_list[0].join(data_str)
            value = eval(value)
            if value:
                break
        return value


class FuncBase(Indicators):
    def __init__(self, market_event, field):
        super().__init__(market_event)
        self.data_dict = DataInClassDict()
        self.data_dict['func'] = 'funcname'
        self.data_dict['arg'] = [field]


class Max(FuncBase):
    def __init__(self, field):
        super().__init__(field)
        self.data_dict['func'] = 'max'


class Min(FuncBase):
    def __init__(self, field):
        super().__init__(field)
        self.data_dict['func'] = 'min'


class Abs(FuncBase):
    def __init__(self, field):
        super().__init__(field)
        self.data_dict['func'] = 'abs'
        # self.data_dict['arg'] = field


class MovingAverage(FuncBase):
    def __init__(self, field):
        super().__init__(field)
        self.data_dict['func'] = 'moving_average'


def moving_average(arg, period=1):
    """怎么定义？？？"""
    if isinstance(arg, Indicators):
        # 保存当前的和前一日期的简单移动平均值
        ma_list = []
        ma_list.append(arg.get_basic_data(period + 1, arg.field)[:-1])
        ma_list.append(arg.get_basic_data(period, arg.field))


class IntPart(FuncBase, Indicators):
    def __init__(self, field):
        super().__init__(field)
        self.data_dict['func'] = 'int'


class MaxHigh(FuncBase):
    def __init__(self, field):
        super().__init__(field)
        self.data_dict['func'] = 'max_high'


class MinLow(FuncBase):
    def __init__(self, field):
        super().__init__(field)
        self.data_dict['func'] = 'min_low'


class CrossUp(FuncBase):
    def __init__(self, field):
        super().__init__(field)
        self.data_dict['func'] = 'crossup'


class CrossDown(FuncBase):
    def __init__(self, field):
        super().__init__(field)
        self.data_dict['func'] = 'crossdown'


class FindMaxPeriod(object):
    """获取计算公式中的最大周期"""
    def __init__(self):
        self._period = []

    def find(self, dic):
        for key, value in dic.items():
            if key is 'func':
                pass
            if key is 'arg':  # value 是一个列表
                # logger.debug('lenth of value: {}'.format(value))
                for i in value:
                    logger.debug('i:', i)
                    if isinstance(i, int) or isinstance(i, float):
                        self._period.append(i)
                        logger.debug('append: {}'.format(i))
                        # continue
                    elif isinstance(i, dict):
                        self.find(i)  # 只要是字典，一定会返回一个值，否则报错
                        # continue
                    else:
                        self._period.append(0)
                        logger.debug('else: {}'.format(i))
        return max(self._period)


# class MaxHigh(Indicators):
#     def __init__(self, market_event):
#         super().__init__(market_event)
#         self.market_event = market_event
#
#     def data(self, period):
#         high = self.get_basic_data(period, ohlc='high')
#         self.high = max(high)
#         return MaxHigh(self.market_event)
#
#     def data_list(self):
#         max_high_list = []
#         # 最近三个period周期内的最高价
#         for i in range(3):
#             if i == 0:
#                 max_high_data = max(self.get_basic_data(self.period))
#             else:
#                 max_high_data = max(self.get_basic_data(self.period + i)[:-i])
#             max_high_list.append(max_high_data)
#         self.max_high_list = max_high_list
#         return MaxHigh(self.market_event)
#
#
# class MinLow(Indicators):
#     def __init__(self, market_event):
#         super().__init__(market_event)
#
#     def data(self, period):
#         low = self.get_basic_data(period, ohlc='low')
#         return max(low)
#
#     def data_list(self):
#         min_low_list = []
#         # 最近三个period周期内的最高价
#         for i in range(3):
#             if i == 0:
#                 min_low_data = max(self.get_basic_data(self.period))
#             else:
#                 min_low_data = max(self.get_basic_data(self.period + i)[:-i])
#             min_low_list.append(min_low_data)
#         return min_low_list


# class Cross(Indicators):
#     def __init__(self, market_event):
#         super().__init__(market_event)
#
#     def crossup(self, arg1, arg2):
#         if isinstance(arg1, Indicators) and isinstance(arg2, Indicators):
#             arg1_list = arg1.data_list()
#             arg2_list = arg2.data_list()
#             if arg1_list[-1] > arg2_list[-1]:
#                 if arg1_list[-2] == arg2_list[-2]:
#                     if arg1_list[-3] < arg2_list[-3]:
#                         return True
#                 if arg1_list[-2] < arg2_list[-2]:
#                     return True
#             else:
#                 return False
#         else:
#             return False
#
#     def crossdown(self, arg1, arg2):
#         if isinstance(arg1, Indicators) and isinstance(arg2, Indicators):
#             arg1_list = arg1.data_list()
#             arg2_list = arg2.data_list()
#             if arg1_list[-1] < arg2_list[-1]:
#                 if arg1_list[-2] == arg2_list[-2]:
#                     if arg1_list[-3] > arg2_list[-3]:
#                         return True
#                 if arg1_list[-2] > arg2_list[-2]:
#                     return True
#             else:
#                 return False
#         else:
#             return False
#
#
# class AverageTrueRange(Indicators):
#     def __init__(self, market_event):
#         super().__init__(market_event)
#         self.high = High(market_event)
#         self.low = Low(market_event)
#         self.close = Close(market_event)
#
#     def data(self, period):
#         tr_list = []
#         _high = self.high.data_list(period)  # period周期内的最高价
#         _low = self.low.data_list(period)  # period周期内的最低价
#         _close = self.close.data_list(period + 1)  # period+1周期内的收盘价
#         for i in range(period):
#             true_range = max(
#                 _high[i] - _low[i], abs(_close[i] - _high[i]), abs(_close[i] - _low[i]))
#             tr_list.append(true_range)
#         atr = sum(tr_list) / period
#         return atr
#
#
# class MovingAverage(Indicators):
#     """
#     收盘价的简单移动平均值
#     """
#     def __init__(self, marketevent):
#         super().__init__(marketevent)
#
#     def data(self, period):
#         low = self.get_basic_data(period, ohlc='close')
#         return max(low)
#
#     def data_list(self):
#         moving_average_list = []
#         # 最近三个period周期内的收盘价的简单移动平均值
#         for i in range(3):
#             if i == 0:
#                 moving_average_data = max(self.get_basic_data(self.period))
#             else:
#                 moving_average_data = max(self.get_basic_data(self.period + i)[:-i])
#             moving_average_list.append(moving_average_data)
#         return moving_average_list


# class Tree(object):
#     def __init__(self, name='root', children=None):
#         self.name = name
#         self.children = []
#         if children is not None:
#             for child in children:
#                 self.add_child(child)
#
#     def __repr__(self):
#         return self.name
#
#     def add_child(self, node):
#         assert isinstance(node, Tree)
#         self.children.append(node)
#
#
# class MarketPrice(IndicatorBase, Tree):
#     def __init__(self, market_event):
#         super().__init__(market_event)
#
#     def data(self, period, ohlc):
#         data = self.get_basic_data(period, ohlc)
