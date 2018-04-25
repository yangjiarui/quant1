# coding:utf-8
import queue
from collections import OrderedDict
from event import events
from backtestfill import BacktestFill
from dict_to_table import dict_to_table
from barbase import Bar


class Quant(object):
    def __init__(self):
        self.feed_list = []
        self.strategy_list = []
        self.bar = None
        self.portfolio = None
        self.broker = None
        self.fill = None

    def run(self):
        """主循环"""
        self.__initialization()
        pass

    def __initialization(self):
        """对所有 feed 和 fill 内各项数据进行初始化"""
        for feed in self.feed_list:
            feed.run_once()
            instrument = feed.instrument
            self.fill.position.initialize(instrument, 0)
            self.fill.margin.initialize(instrument, 0)
            self.fill.commission.initialize(instrument, 0)
            self.fill.avg_price.initialize(instrument, 0)
            self.fill.unrealized_gain_and_loss.initialize(instrument, 0)
            self.fill.realized_gain_and_loss.initialize(instrument, 0)
        self.fill.cash.initialize('all', self.fill.initial_cash)
        self.fill.balance.initialize('all', self.fill.initial_cash)

        self.__combine_all_feed()

    def __combine_all_feed(self):
        """只运行一次，创建一个空Bar，然后将所有feed都整合到一起"""
        self.bar = Bar('')
        self.bar._initialize()
        for feed in self.feed_list:
            self.bar._combine_all_feed(feed.bar.total_dict)

    def __load_all_feed(self):
        """加载新行情"""
        for feed in self.feed_list:
            feed.start()
            feed.prenext()
            feed.next()

    def __update_time_index(self):
        """每次更新行情后，根据新行情更新仓位、现金、保证金等账户基本信息"""
        self.fill.update_time_index(self.feed_list)
        date_dict = {}
        if len(self.feed_list) > 1:
            for index, feed in enumerate(self.feed_list):
                date_dict[str(index)] = feed.cur_bar.cur_date
                if self.feed_list.count(feed) > 1:
                    raise SyntaxError('行情中出现了相同的日期，数据有误')

    def __check_pending_order(self):
        """检查止盈、止损、移动止损、挂单是否成交"""
        for feed in self.feed_list:
            self.fill.check_trade_list(feed)
            self.fill.check_order_list(feed)

    def __pass_to_market(self, market_event):
        """传递账户基本信息给各模块使用"""
        market_event.fill = self.fill
        self.portfolio.fill = self.fill
        self.broker.fill = self.fill

    def __check_backtest_finished(self):
        """检查回测是否结束，如果结束了，返回True"""
        backtest = [i.continue_backtest for i in self.feed_list]
        return not sum(backtest)
