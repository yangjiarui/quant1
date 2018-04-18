# coding:utf-8
import abc
from event import events, SignalEvent
from indicator import Indicator
from order import BuyOrder, SellOrder, ExitAllOrder


class StrategyBase(abc.ABCMeta):
    def __init__(self, market_event):
        self._signal_list = []
        self.market_event = market_event

        self.mult = market_event.mult
        self.instrument = market_event.instrument
        self.bar = market_event.bar
        self.bar.set_instrument(self.instrument)

    def buy(self, units, price=None, instrument=None):
        buy_order = BuyOrder(self.marketevent)
        buy_order.execute(units=units, price=price, instrument=instrument)
        self._signal_list.append(SignalEvent(buy_order))
    
    def sell(self, units, price=None, instrument=None):
        sell_order = SellOrder(self.marketevent)
        sell_order.execute(units=units, price=price, instrument=instrument)
        self._signal_list.append(SignalEvent(sell_order))

    def exitall(self, instrument=None, price=None):
        exit_all_order = ExitallOrder(self.marketevent)
        if self.position[-1] < 0:
            exit_all_order.set_order_type('Buy')
        elif self.position[-1] > 0:
            exit_all_order.set_order_type('Sell')
        else:
            exit_all_order.set_order_type('Sell')
            return
        
        units = abs(self.position[-1])
        exit_all_order.execute(units=units, price=price, instrument=instrument)
        self._signal_list.append(SignalEvent(exit_all_order))

    def cancel(self):
        pass
    
    def __start(self):
        self.__set_dataseries_instrument()
        self.__set_indicator()

    def prenext(self):
        pass

    @abc.abstractmethod
    def next(self):
        """
        编写主要策略
        """
        pass

    def __prestop(self):
        """
        若做多做空和一键平仓同时出现,则一键平仓
        """
        for signal in self._signal_list:
            if signal.exectype == 'CloseAll':
                self._signal_list = [] if signal.units == 0 else [signal]
                break
        for signal in self._signal_list:
            if signal.instrument is self.instrument:
                events.put(signal)

    def stop(self):
        pass

    def run_strategy(self):
        self.__start()
        self.__prestop()
        self.stop()
