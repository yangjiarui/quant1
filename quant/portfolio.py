# coding:utf-8
from quant.event import OrderEvent, events
from quant.context import Context


class PortfolioBase(object):
    """处理信号的基类"""
    def __init__(self):
        self.signal_event = None

    def generate_order(self):
        order = self.signal_event.order
        order_event = Context().OrderEvent
        events.put(order_event(order))

    def run_portfolio(self, signal_event):
        self.signal_event = signal_event
        self.generate_order()


class Portfolio(PortfolioBase):
    pass
