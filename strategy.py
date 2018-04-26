# coding:utf-8
from abc import ABC, abstractmethod
from event import events, SignalEvent
from indicator import Indicator
from order import BuyOrder, SellOrder, ExitAllOrder
from logging_backtest import logger


class StrategyBase(ABC):
    """策略基类"""

    def __init__(self, market_event):
        self._signal_list = []
        self.market_event = market_event

        self.mult = market_event.mult
        self.instrument = market_event.instrument
        self.bar = market_event.bar
        self.bar.set_instrument(self.instrument)
        self.position = market_event.fill.position
        self.margin = market_event.fill.margin
        self.avg_price = market_event.fill.avg_price
        self.unrealized_gain_and_loss = market_event.fill.unrealized_gain_and_loss
        self.realized_gain_and_loss = market_event.fill.realized_gain_and_loss
        self.commision = market_event.fill.commision
        self.cash = market_event.fill.cash
        self.balance = market_event.fill.balance

    def __set_dataseries_instrument(self):
        """确保dataseries对应的instrument为正在交易的品种"""
        self.position.set_instrument(self.instrument)
        self.margin.set_instrument(self.instrument)
        self.avg_price.set_instrument(self.instrument)
        self.unrealized_gain_and_loss.set_instrument(self.instrument)
        self.realized_gain_and_loss.set_instrument(self.instrument)
        self.commision.set_instrument(self.instrument)

    def __set_indicator(self):
        """设置技术指标"""
        self.indicator = Indicator(self.market_event)

    def points(self, n):
        """
        数值：在price中可正可负，判断是否为挂单。其余只可为正。
        单位：元。
        说明：作为take_profit、stop_loss，trailing_stop、price的参数使用，
             实现止盈止损和挂单。
        """
        points = type('points', (), dict(points=n))
        points.type = 'points'
        return points

    def pct(self, n):
        """
        数值：在price中可正可负，判断是否为挂单。其余只可为正。
        单位：无。
        说明：作为take_profit、stop_loss，trailing_stop、price的参数使用，
             实现止盈止损和挂单。
        示例：若输入1，则为原价格的1%
        """
        n = n * 0.01  # 换算为百分数
        pct = type('pct', (), dict(pct=n))
        pct.type = 'pct'
        return pct

    def buy(self,
            units,
            instrument=None,
            price=None,
            take_profit=None,
            stop_loss=None,
            trailing_stop=None):
        buy_order = BuyOrder(self.market_event)
        buy_order.execute(
            instrument=instrument,
            units=units,
            price=price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            trailing_stop=trailing_stop)
        self._signal_list.append(SignalEvent(buy_order))

    def sell(self,
             units,
             instrument=None,
             price=None,
             take_profit=None,
             stop_loss=None,
             trailing_stop=None):
        sell_order = SellOrder(self.market_event)
        sell_order.execute(
            instrument=instrument,
            units=units,
            price=price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            trailing_stop=trailing_stop)
        self._signal_list.append(SignalEvent(sell_order))

    def exit_all(self, instrument=None, price=None):
        exit_all_order = ExitAllOrder(self.market_event)
        # 仓位为负，说明是卖出开仓的，需买入平仓
        if self.position[-1] < 0:
            exit_all_order.set_order_type('Buy')
        # 仓位为正，说明是买入开仓的，需卖出平仓
        elif self.position[-1] > 0:
            exit_all_order.set_order_type('Sell')
        # 仓位为0，不需要操作，但为防止触发其他单，返回空
        else:
            exit_all_order.set_order_type('Sell')
            return

        units = abs(self.position[-1])
        exit_all_order.execute(
            instrument=instrument,
            units=units,
            price=price,
            take_profit=None,
            stop_loss=None,
            trailing_stop=None)
        self._signal_list.append(SignalEvent(exit_all_order))

    def cancel(self):
        pass

    def __start(self):
        self.__set_dataseries_instrument()
        self.__set_indicator()

    def prenext(self):
        pass

    @abstractmethod
    def next(self):
        """
        编写主要策略的地方，需要在子类中重写
        """
        pass

    def __prestop(self):
        """
        若做多做空和一键平仓同时出现,则一键平仓
        """
        for signal in self._signal_list:
            if signal.execute_type == 'CLOSE_ALL':
                self._signal_list = [] if signal.units == 0 else [signal]
                break
        for signal in self._signal_list:
            if signal.instrument is self.instrument:
                events.put(signal)

    def stop(self):
        pass

    def __preposs(self):

        try:
            self.prenext()
            self.next()
        except Warning:
            date = str(self.market_event.cur_bar.cur_date)
            logger.info('{} 信号不够，不发生交易'.format(date))
        except IndexError:
            date = str(self.market_event.cur_bar.cur_date)
            logger.info('{} 数据不够，不发生交易'.format(date))

    def run_strategy(self):
        self.__start()
        self.__preposs()
        self.__prestop()
        self.stop()
