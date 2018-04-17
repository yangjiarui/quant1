# coding:utf-8
import queue

events = queue.Queue()


class EventBase(object):
    """
    传递各种事件，把order的属性传给event，并设定event的相关属性，包括：
    feed, date, instrument, 
    """

    def __init__(self, order):
        self._order = order

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, value):
        self._order = value

    @property
    def feed(self):
        return self._order.feed

    @feed.setter
    def feed(self, value):
        self._order.set_feed(value)

    @property
    def units(self):
        return self._order.units

    @units.setter
    def units(self, value):
        self._order.set_units(value)

    @property
    def execute_type(self):
        return self._order.execute_type

    @execute_type.setter
    def execute_type(self, value):
        self._order.set_execute_type(value)

    @property
    def price(self):
        return self._order.price

    @price.setter
    def price(self, value):
        self._order.set_price(value)    

    @property
    def order_type(self):
        return self._order.order_type

    @order_type.setter
    def order_type(self, value):
        self._order.set_order_type(value)

    @property
    def date(self):
        return self._order.date

    @date.setter
    def date(self, value):
        self._order.set_date(value)

    @property
    def instrument(self):
        return self._order.instrument

    @instrument.setter
    def instrument(self, value):
        self._order.set_instrument(value)

    @property
    def per_comm(self):
        return self._order.per_comm

    @per_comm.setter
    def per_comm(self, value):
        self._order.set_per_comm(value)

    @property
    def per_margin(self):
        return self._order.per_comm

    @per_margin.setter
    def per_margin(self, value):
        self._order.set_per_margin(value)

    @property
    def mult(self):
        return self._order.mult

    @mult.setter
    def mult(self, value):
        self._order.set_mult(value)


class MarketEvent(object):
    """
    市场信息事件，该事件会被传给Strategy
    """
    def __init__(self, feed):
        self.type = 'Market'
        self.feed = feed
        self.instrument = feed.instrument
        self.cur_bar = feed.cur_bar
        self.bar = feed.bar
        self.per_comm = feed.per_comm
        self.per_margin = feed.per_margin
        self.mult = feed.mult


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
