import numpy as np
from copy import copy
import talib

# raw_data[0]: high_raw_data, raw_data[1]: low_raw_data, raw_data[2]: close_raw_data
raw_data = [
    [2554.4, 2548.8, 2543.8, 2562.2, 2547.8, 2598.2, 2608.6, 2602.8, 2593, 2628, 2621, 2616.8, 2616.2, 2673.6, 2601.2,
     2660.6, 2687.4, 2700.4, 2703.6, 2753.8],
    [2523.2, 2506.6, 2509, 2512.6, 2481.8, 2489.8, 2583, 2528, 2548.6, 2565.2, 2587, 2579.2, 2582.4, 2572.8, 2581.6,
     2590.4, 2653.6, 2661.2, 2676.6, 2675.2],
    [2533.2, 2531.2, 2525.4, 2537.8, 2498.6, 2586.6, 2596.4, 2570, 2576.8, 2610.4, 2608.2, 2602.6, 2615.6, 2590.6,
     2592.8, 2654.4, 2671, 2699, 2699.8, 2746.4]
]


class Indicators(object):
    def __init__(self, field=None, period=1):
        self.field = field
        self.period = period
        self.data_dict = {'arg': [], 'func': []}

    def get_real_data(self):
        """
        根据period获取数据，period为1，获取当天的数据，
        period为2，获取前一天的数据，以此类推
        """
        if self.field == 'high':
            data = raw_data[0][-self.period]
        elif self.field == 'low':
            data = raw_data[1][-self.period]
        elif self.field == 'close':
            data = raw_data[2][-self.period]
        else:
            data = None
        return data

    def get_real_data_list(self):
        """
        根据period获取数据，period为1，获取当天的数据，
        period为2，获取前一天的数据和当天的数据，以此类推
        返回一个列表
        """
        if self.field == 'high':
            data_list = raw_data[0][-self.period:]
        elif self.field == 'low':
            data_list = raw_data[1][-self.period:]
        elif self.field == 'close':
            data_list = raw_data[2][-self.period:]
        else:
            data_list = None
        return data_list

    def __add__(self, other):
        """类 + other, 类指的是Indicators, 下同"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = '+'
        another.data_dict['arg'].append(other)
        return another

    def __sub__(self, other):
        """类 - other"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = '-'
        another.data_dict['arg'].append(other)
        return another

    def __mul__(self, other):
        """类 × other"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = '*'
        another.data_dict['arg'].append(other)
        return another

    def __truediv__(self, other):
        """类 / other"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = '/'
        another.data_dict['arg'].append(other)
        return another

    def __radd__(self, other):
        """other + 类"""
        another = Indicators()
        another.data_dict['arg'].append(other)
        another.data_dict['func'] = '+'
        another.data_dict['arg'].append(self)
        return another

    def __rsub__(self, other):
        """other - 类"""
        another = Indicators()
        another.data_dict['arg'].append(other)
        another.data_dict['func'] = '-'
        another.data_dict['arg'].append(self)
        return another

    def __rmul__(self, other):
        """other × 类"""
        another = Indicators()
        another.data_dict['arg'].append(other)
        another.data_dict['func'] = '*'
        another.data_dict['arg'].append(self)
        return another

    def __rtruediv__(self, other):
        """other / 类"""
        another = Indicators()
        another.data_dict['arg'].append(other)
        another.data_dict['func'] = '/'
        another.data_dict['arg'].append(self)
        return another

    def __abs__(self):
        """abs(类)"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'abs'
        return another

    def max(self, *args):
        """Indicators.max(类, *args)"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'max'
        another.data_dict['arg'] += [*args]
        return another

    def min(self, *args):
        """Indicators.min(类, *args)"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'min'
        another.data_dict['arg'] += [*args]
        return another

    def int_part(self):
        """Indicators.int_part(类)"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'int'
        return another

    def max_high(self, *args):
        """Indicators.max_high(类, *args)"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'max_high'
        another.data_dict['arg'] += [*args]
        return another

    def min_low(self, *args):
        """Indicators.min_low(类, *args)"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'min_low'
        another.data_dict['arg'] += [*args]
        return another

    def cross_up(self, *args):
        """Indicators.cross_up(类, *args)"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'cross_up'
        another.data_dict['arg'] += [*args]
        return another

    def cross_down(self, *args):
        """Indicators.cross_down(类, *args)"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'cross_down'
        another.data_dict['arg'] += [*args]
        return another

    def moving_average(self, period):
        """简单移动平均值"""
        another = Indicators()
        another.data_dict['arg'].append(self)
        another.data_dict['func'] = 'moving_average'
        another.data_dict['arg'] += [period]
        return another


class Evaluate(object):
    """判断买入卖出时机时，进行解析"""

    def __init__(self, unevaluated: Indicators):
        self.func_list = []
        self.data_dict = copy(unevaluated.data_dict)
        self.data = []  # 暂时存储计算数据

    def get_func(self):
        for key, value in self.data_dict.items():
            if value is 'func':
                self.func_list.append(value)

    def evaluate(self):
        while True:
            value = 'None'
            if len(self.data_dict['func']):
                self.func_list.append(self.data_dict['func'])
                self.data_dict['func'] = []
            else:
                for i in self.data_dict['arg']:
                    if isinstance(i, Indicators):
                        self.data.append(i.get_real_data())
                    elif isinstance(i, int):
                        self.data.append(i)
            if self.func_list[0] in ['+', '-', '*', '/']:
                if self.data:
                    data_str = [str(i) for i in self.data]
                    value = self.func_list[0].join(data_str)
            elif self.func_list[0] in ['moving_average']:
                if self.data:
                    field = np.array(self.data[:-1])
                    period = self.data[-1]
                    value = self.moving_average(field, period)
            value = eval(value)
            if value:
                break
        return value

    def moving_average(self, field, period):
        """简单移动平均"""
        sma = talib.SMA(field, period)  # 返回array，period个数前计算会得到nan，需处理
        if np.isnan(sma[-1]):
            raise Warning
        else:
            return sma[-1]

"""
待实现的功能：嵌套结构中外层函数调用底层的数据

整个数据结构都是自定义的Indicators类，类中的字典data_dict储存数据，data_dict: {'arg': [], 'func': []}。
自定义了类的运算，使得类相运算后仍然返回类，如：high、low均为Indicators类，high – low 返回一个类，
其data_dict = {'arg': [high, low], 'func': ['-']}，这样就实现了数据储存，待最后需要计算的时候再提取进行计算。
已实现了底层的数据计算，如 high – low，计算得到单个值。
再往上一层，如下例中，tr, atr, 该怎么计算(atr为计算tr的5日简单移动平均，即前5日的tr的平均值)。
特殊的，crossup、crossdown，该怎么处理日期问题。

"""
high = Indicators('high')
low = Indicators('low')
close = Indicators('close')
arg1 = high - low
arg1_value = Evaluate(arg1).evaluate()
print(arg1_value)  # 最底层已实现取值

close_ref = Indicators('close', 2)
arg2 = abs(close_ref - high)
arg3 = abs(close_ref - low)
tr = Indicators.max(arg1, arg2, arg3)  # 上一层如何取值
atr = Indicators.moving_average(tr, 5)  # 这里，需要底层取前5日的值，而不是一个值
ma5 = Indicators.moving_average(close, 5)
ma10 = Indicators.moving_average(close, 10)
# 5日均线上穿10日均线为买入信号，意味着起码要取两个ma5和两个ma10，
# 即当天的ma5（前5天的值）和昨天的ma5（前6天到昨天的值），ma10同理
buy_ = Indicators.cross_up(ma5, ma10)
