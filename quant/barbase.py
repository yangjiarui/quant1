# coding:utf-8
import pandas as pd
from quant.logging_backtest import logger
from datetime import datetime





class BarBase(object):
    pass


class Current_bar(BarBase):
    """当前bar的数据，以列表储存，只有一条，为当前行情，并把这些数据设为类属性"""
    def __init__(self):
        self._cur_bar_list = [0]

    def add_new_bar(self, new_bar):
        """不断更新当前行情数据"""

        bar_date = datetime.strptime(new_bar['time'], '%Y/%m/%d')
        logger.debug('---bar_date in barbase---: {}'.format(bar_date))
        # bar_list_length = len(self._cur_bar_list)
        logger.debug('self._cur_bar_list in barbase: {}'.format(self._cur_bar_list))
        # if bar_list_length == 2:
        #     # self._cur_bar_list.pop(0)
        #     self._cur_bar_list = []
        # elif bar_list_length == 1:
        #     if new_bar['time'] == self._cur_bar_list[0]['time']:
        #         self._cur_bar_list = []
        # self._cur_bar_list.append(new_bar)
        self._cur_bar_list[0] = new_bar

    @property
    def cur_data(self):
        return self._cur_bar_list[0]

    # @property
    # def next_data(self):
    #     return self._cur_bar_list[1]

    @property
    def cur_date(self):
        return self._cur_bar_list[0]["time"]

    @property
    def cur_open(self):
        return self._cur_bar_list[0]["open"]

    @property
    def cur_high(self):
        return self._cur_bar_list[0]["high"]

    @property
    def cur_low(self):
        return self._cur_bar_list[0]["low"]

    @property
    def cur_close(self):
        return self._cur_bar_list[0]["close"]

    # @property
    # def next_date(self):
    #     return self._cur_bar_list[1]["time"]

    # @property
    # def next_open(self):
    #     return self._cur_bar_list[1]["open"]

    # @property
    # def next_high(self):
    #     return self._cur_bar_list[1]["high"]

    # @property
    # def next_low(self):
    #     return self._cur_bar_list[1]["low"]

    # @property
    # def next_close(self):
    #     return self._cur_bar_list[1]["close"]


class Bar(BarBase):
    """存储feed中的OHLC数据（open, high, low, close）
    一个instrument对应bar_dict中的一个值
    """

    def __init__(self, instrument):
        self._bar_dict = {instrument: []}
        self._instrument = instrument
        self._data_name = None

    def __getitem__(self, item):
        return self._bar_dict

    def _initialize(self):
        """清空数据"""
        self._bar_dict = {}

    def _combine_all_feed(self, new_bar_dict):
        """只运行一次，将所有feed整合到一起"""
        self._bar_dict.update(new_bar_dict)

    def __getitem_func(self, given):
        if isinstance(given, slice):
            """处理切片对象"""
            if given.start and given.stop:
                start = given.start
                stop = given.stop
            else:
                start = 0
                stop = len(self.data)  # 通过属性定义

            # 切片为负时的情况
            length = len(self.data)
            if start < 0 and stop < 0:
                start = length + start
                stop = length + stop
            original_data = self.data[start:stop]  # 格式为[{},{},{}...]
            data = [i[self._data_name] for i in original_data]
            return data
        else:
            return self._bar_dict[self.instrument][given]["close"]

    def __create_data_cls(self):
        """产生一个新类型，类名为OHLC"""
        cls = type("OHLC", (), {})
        cls.data = self._bar_dict[self.instrument]
        cls.__getitem__ = self.__getitem_func
        return cls

    def set_instrument(self, instrument):
        self._instrument = instrument

    def add_new_bar(self, new_bar):
        self._bar_dict[self.instrument].append(new_bar)

    @property
    def instrument(self):
        return self._instrument

    @property
    def data(self):
        return self._bar_dict[self.instrument]

    @property
    def total_dict(self):
        return self._bar_dict

    @property
    def df(self):
        return pd.DataFrame(self._bar_dict[self.instrument])

    @property
    def open(self):
        self._data_name = "open"
        cls = self.__create_data_cls()
        return cls()

    @property
    def high(self):
        self._data_name = "high"
        cls = self.__create_data_cls()
        return cls()

    @property
    def low(self):
        self._data_name = "low"
        cls = self.__create_data_cls()
        return cls()

    @property
    def close(self):
        self._data_name = "close"
        cls = self.__create_data_cls()
        return cls()
