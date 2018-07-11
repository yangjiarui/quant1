# coding:utf-8
from quant.event import MarketEvent, SignalEvent, OrderEvent, FillEvent
# from quant.broker import Broker
# from quant.backtestfill import BacktestFill
# from quant.portfolio import Portfolio


class Context(object):
    """context，全局变量，包含策略运行的各种信息"""
    def __init__(self):
        self.MarketEvent = MarketEvent
        self.SignalEvent = SignalEvent
        self.OrderEvent = OrderEvent
        self.FillEvent = FillEvent

        self.start_date = None
        self.end_date = None
        self.feed_list = []
        # self.portfolio = Portfolio
        self.portfolio = None
        self.fill = None
        # self.broker = Broker
        # self.fill = BacktestFill
        self.strategy = []
        self.commission = 0
        self.margin = 0.2
        self.units = 300
        self.lots = 1
        self.instrument = 'IF'
        self.initial_cash = 500000

        self.market_event = []
        self.signal_event = []
        self.order_event = []
        self.fill_event = []
        self.count = 0
        self.test_days = 0
        self.ohlc_data = None

# 在 main 里调用，feed，order？
# order 根据不同的情况值不同，也就是说这几个事件的调用是不同步的，不能单纯地把这几个
# 事件集成到Context 里，MarketEvent 在 feedbase 里调用，SignalEvent 在 strategy 里调用，
# OrderEvent 在 portfolio 里调用，FillEvent 在 broker 里调用
#
# context = Context(MarketEvent(feed), SignalEvent(order), OrderEvent(order), FillEvent(order))
