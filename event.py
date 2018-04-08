# coding:utf-8
import queue

events = queue.Queue()


class EventBase(object):
    """
    传递各种事件
    """

    def __init__(self, order):
        self._order = order


class MarketEvent(object):
    """
    市场信息事件，该事件会被传给Strategy
    """
    def __init__(self, data):
        self.type = 'Market'
        self.data = data

class SignalEvent(EventBase):
    """
    交易信号事件，该事件会被传给Portfolio
    """
    def __init__(self, order):
        super(SignalEvent, self).__init__(order)
        self.type = 'Signal'


class OrderEvent(EventBase):
    """
    交易信息事件，该事件会被传给Execution
    """
    def __init__(self, order):
        super(OrderEvent, self).__init__(order)
        self.type = 'Order'


class RecordEvent(EventBase):
    """
    完成交易后产生的事件，该事件将信息集合成交易记录
    """
    def __init__(self, order):
        super(RecordEvent, self).__init__(order)
        self.type = 'Record'