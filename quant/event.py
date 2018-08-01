# coding:utf-8
import queue
from quant.logging_backtest import logger

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

    # @feed.setter
    # def feed(self, value):
    #     self._order.set_feed(value)

    @property
    def lots(self):
        return self._order.lots

    @lots.setter
    def lots(self, value):
        self._order.set_lots(value)

    @property
    def slippage(self):
        return self._order.slippage

    @slippage.setter
    def slippage(self, value):
        self._order.set_slippage(value)

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
    def take_profit(self):
        return self._order.take_profit

    @take_profit.setter
    def take_profit(self, value):
        self._order.set_take_profit(value)

    @property
    def stop_loss(self):
        return self._order.stop_loss

    @stop_loss.setter
    def stop_loss(self, value):
        self._order.set_stop_loss(value)

    @property
    def trailing_stop(self):
        return self._order.trailing_stop

    @trailing_stop.setter
    def trailing_stop(self, value):
        self._order.set_trailing_stop(value)

    @property
    def instrument(self):
        return self._order.instrument

    @instrument.setter
    def instrument(self, value):
        self._order.set_instrument(value)

    @property
    def direction(self):
        return self._order.direction

    @direction.setter
    def direction(self, value):
        self._order.set_direction(value)

    @property
    def status(self):
        return self._order.status

    @status.setter
    def status(self, value):
        self._order.set_status(value)

    @property
    def per_comm(self):
        return self._order.per_comm

    @per_comm.setter
    def per_comm(self, value):
        self._order.set_per_comm(value)

    @property
    def per_margin(self):
        return self._order.per_margin

    @per_margin.setter
    def per_margin(self, value):
        self._order.set_per_margin(value)

    @property
    def units(self):
        return self._order.units

    @units.setter
    def units(self, value):
        self._order.set_units(value)

    @property
    def bs_price(self) -> list:
        """buy and sell price list"""
        return self._order.bs_price

    @bs_price.setter
    def bs_price(self, value) -> list:
        return self._order.set_bs_price(value)


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
        # logger.debug('self.bar.open[:] in event: {}'.format(self.bar.open[:]))
        self.per_comm = feed.per_comm
        self.per_margin = feed.per_margin
        self.units = feed.units
        self.execute_mode = feed.execute_mode
        self.slippage = feed.slippage
        logger.info('---slippage in event---:{}'.format(self.slippage))


class SignalEvent(EventBase):
    """
    交易信号事件，该事件会被传给Portfolio
    """
    def __init__(self, order):
        super().__init__(order)
        self.type = 'Signal'


class OrderEvent(EventBase):
    """
    交易信息事件，该事件会被传给Broker
    """
    def __init__(self, order):
        super().__init__(order)
        self.type = 'Order'


class FillEvent(EventBase):
    """
    记录交易事件
    """
    def __init__(self, order):
        super().__init__(order)
        self.type = 'Fill'
