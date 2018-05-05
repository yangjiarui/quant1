# coding:utf-8
from quant.event import OrderEvent, events


class PortfolioBase(object):
    """处理信号的基类"""
    def __init__(self):
        self.signal_event = None

    def generate_order(self):
        order = self.signal_event.order
        events.put(OrderEvent(order))

    def run_portfolio(self, signal_event):
        self.signal_event = signal_event
        self.generate_order()


class Portfolio(PortfolioBase):
    pass
