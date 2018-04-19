# coding=utf-8
from abc import ABC, abstractmethod
from datetime import datetime
import csv
from barbase import Current_bar, Bar
from event import events, MarketEvent


class DataHandler(ABC):
    def __init__(self, instrument, startdate, enddate):
        self.instrument = instrument
        self.startdate = startdate
        self.enddate = enddate

        self.cur_bar = Current_bar()
        self.bar = Bar(instrument)
        self.preload_bar_list = []
        self.continue_backtest = True

        self._per_comm = None
        self._per_margin = None
        self._mult = None
        self._iteration_buffer = None  # 给preload用的，一次性的
        self._buffer_days = None
        self._iteration_data = None  # 给get_new_bar用的

    def set_per_comm(self, value):
        self._per_comm = value

    def set_per_margin(self, value):
        self._per_margin = value

    def set_iteration_buffer(self, value):
        self._iteration_buffer = value

    def set_buffer_days(self, value):
        self._buffer_days = value

    def set_mult(self, value):
        self._mult = value

    @property
    def per_comm(self):
        return self._per_comm

    @property
    def per_margin(self):
        return self._per_margin

    @property
    def mult(self):
        return self._mult

    @property
    def _iteration_buffer(self):
        return self._iteration_buffer

    @abstractmethod
    def load_data(self):  # 读取数据，需重写
        pass

    @abstractmethod
    def get_new_bar(self):  # 加载新数据，需重写
        pass

    @abstractmethod
    def preload(self):  # 缓存数据，需重写
        pass

    def load_once(self):  # 加载一次，使cur_bar缓存数据
        self._iteration_data = self.load_data()

    def __update_bar(self):  # 更新bar
        self.bar.set_instrument(self.instrument)
        self.bar.add_new_bar(self.cur_bar.cur_data)

    def start(self):
        pass

    def prenext(self):
        self.get_new_bar()

    def next(self):
        self.__update_bar()
        events.put(MarketEvent(self))


class CSVDataReader(DataHandler):
    """识别csv数据中的数据，包括date、open、high、low、close"""
    date_format = '%Y/%m/%d %H:%M:%S'

    def __init__(self, datapath, instrument, startdate=None, enddate=None):
        super().__init__(self, instrument, startdate, enddate)

        self.datapath = datapath

    def __set_date(self):
        """将输入的日期转换成datetime对象"""
        if self.startdate:
            self.startdate = datetime.strptime(self.startdate,
                                               "%Y-%m-%d %H:%M")
        if self.enddate:
            self.enddate = datetime.strptime(self.enddate, "%Y-%m-%d %H:%M")

    def __set_bar_date(self, bar):
        """将bar中的date识别为日期格式"""
        date = bar['date']
        return datetime.strptime(str(date), self.date_format).strftime(
            self.date_format)

    def get_new_bar(self):
        def __update():
            new_bar = next(self._iteration_data)  # 获取迭代数据的下一组数据
            new_bar['date'] = self.__set_bar_date(new_bar)
            # 将new_bar中的OHLC等数值转换为float
            for i in new_bar:
                try:
                    new_bar[i] = float(new_bar[i])
                except ValueError:
                    pass
            return new_bar

        try:
            new_bar = __update()
            # 根据输入的日期判断数据的范围，从起始时间开始，不断产生new_bar，到结束时间为止
            if self.startdate:
                while datetime.strptime(new_bar["date"],
                                        self.date_format) < self.startdate:
                    new_bar = __update()
            if self.enddate:
                while datetime.strptime(new_bar["date"],
                                        self.date_format) > self.enddate:
                    raise StopIteration

            self.cur_bar.add_new_bar(new_bar)

        except StopIteration:
            self.continue_backtest = False

    def load_data(self):
        """
        产生一个OrderedDict，第一行作为filedname，即OHLC
        每次调用产生一个新的OrderedDict
        OrderedDict([('date', '2017/5/27 1:32:00'),
                     ('open', '222.2'), ('high', '333.3'),
                     ('low', '111.1'), ('close', '230.4')])
        """
        return csv.DictReader(open(self.datapath))

    def preload(self):
        self.set_iteration_buffer(self.load_data())

        def _update():
            bar = next(self._iteration_buffer)
            bar['date'] = self.__set_bar_date(bar)

            for i in bar:
                try:
                    bar[i] = float(bar[i])
                except ValueError:
                    pass
            return bar

        try:
            bar = _update()
            if self.startdate:
                while datetime.strptime(bar["date"],
                                        self.date_format) < self.startdate:
                    bar = _update()
                    self.preload_bar_list.append(bar)
                else:
                    self.preload_bar_list.pop(-1)  # 经过验证bug检查的，最后删除掉一个重复(暂未证实)

            elif self.startdate is None:
                pass
            else:
                raise SyntaxError("语法错误")

        except IndexError:
            pass

        except StopIteration:
            print("不可能的")

        self.preload_bar_list.reverse()
