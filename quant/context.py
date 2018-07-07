# coding:utf-8
from quant.event import MarketEvent, SignalEvent, OrderEvent, FillEvent


class Context(object):
    """context，全局变量，包含策略运行的各种信息"""
    def __init__(self, market, signal, order, fill):
        self.market = market
        self.signal = signal
        self.order = order
        self.fill = fill


# 在 main 里调用，feed，order？
# order 根据不同的情况值不同，也就是说这几个事件的调用是不同步的，不能单纯地把这几个
# 事件集成到Context 里，MarketEvent 在 feedbase 里调用，SignalEvent 在 strategy 里调用，
# OrderEvent 在 portfolio 里调用，FillEvent 在 broker 里调用
#
context = Context(MarketEvent(feed), SignalEvent(order), OrderEvent(order), FillEvent(order))
