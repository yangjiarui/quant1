# coding:utf-8
from abc import ABC, abstractmethod
from quant.event import events, SignalEvent
from quant.indicator import Indicator  # Open, High, Low, Close, MaxHigh, MinLow
from quant.order import BuyOrder, SellOrder, ExitAllOrder
from quant.logging_backtest import logger


class StrategyBase(ABC):
    """策略基类"""

    def __init__(self, market_event):
        self._signal_list = []
        self.market_event = market_event

        self.units = market_event.units
        self.instrument = market_event.instrument
        self.bar = market_event.bar
        self.bar.set_instrument(self.instrument)
        self.position = market_event.fill.position
        self.margin = market_event.fill.margin
        self.avg_price = market_event.fill.avg_price
        self.unrealized_gain_and_loss = market_event.fill.unrealized_gain_and_loss
        self.realized_gain_and_loss = market_event.fill.realized_gain_and_loss
        self.commission = market_event.fill.commission
        self.cash = market_event.fill.cash
        self.equity = market_event.fill.equity

    def __set_dataseries_instrument(self):
        """确保dataseries对应的instrument为正在交易的品种"""
        self.position.set_instrument(self.instrument)
        self.margin.set_instrument(self.instrument)
        self.avg_price.set_instrument(self.instrument)
        self.unrealized_gain_and_loss.set_instrument(self.instrument)
        self.realized_gain_and_loss.set_instrument(self.instrument)
        self.commission.set_instrument(self.instrument)

    def __set_indicator(self):
        """设置技术指标"""
        self.indicator = Indicator(self.market_event)
        # self.open = Open(self.market_event)
        # self.high = High(self.market_event)
        # self.low = Low(self.market_event)
        # self.close = Close(self.market_event)
        # self.max_high = MaxHigh(self.market_event)
        # self.min_low = MinLow(self.market_event)
        # self.cross = Cross(self.market_event)
        # self.average_true_range = AverageTrueRange(self.market_event)

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

    def buy_base(self,
                 lots,
                 instrument=None,
                 price=None,
                 take_profit=None,
                 stop_loss=None,
                 trailing_stop=None):
        buy_order = BuyOrder(self.market_event)
        buy_order.execute(
            instrument=instrument,
            lots=lots,
            price=price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            trailing_stop=trailing_stop)
        logger.debug('self.position[-1] in buy_base: {}'.format(self.position[-1]))
        self._signal_list.append(SignalEvent(buy_order))

    def sell_base(self,
                  lots,
                  instrument=None,
                  price=None,
                  take_profit=None,
                  stop_loss=None,
                  trailing_stop=None):
        sell_order = SellOrder(self.market_event)
        sell_order.execute(
            instrument=instrument,
            lots=lots,
            price=price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            trailing_stop=trailing_stop)
        logger.debug('self.position[-1] in sell_base: {}'.format(self.position[-1]))
        self._signal_list.append(SignalEvent(sell_order))

    def buy(self,
            lots,
            instrument=None,
            price=None,
            take_profit=None,
            stop_loss=None,
            trailing_stop=None):
        # if self.position[-1] <= 0:  # 只有当未开仓或已建立空仓的情况才能买入
        #     logger.debug('self.position[-1] in buy: {}'.format(self.position[-1]))
        #     self.buy_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
        pass

    def sell(self,
             lots,
             instrument=None,
             price=None,
             take_profit=None,
             stop_loss=None,
             trailing_stop=None):
        # logger.debug('self.position[-1] in sell: {}'.format(self.position[-1]))
        # if self.position[-1] >= 0:  # 只有当未开仓或已建立多仓的情况才能卖出
        #     self.sell_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
        pass

    def buy_even_and_open(self,
                          lots,
                          instrument=None,
                          price=None,
                          take_profit=None,
                          stop_loss=None,
                          trailing_stop=None):
        # logger.debug('self.first_open in strategy: {}'.format(self.first_open))
        # logger.debug('self.position[-1] in strategy: {}'.format(self.position[-1]))
        # if first_open:  # 第一次开仓，只能买入一次
        #     self.buy_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
        #     # self.first_open = False
        #     return
        # logger.debug('self.position[-1] in buy_even_and_open: {}'.format(self.position))
        # if self.position[-1] < 0:  # 只有当已建立空仓的情况下，才能买入平仓并继续买入开多仓
        #     self.buy_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
        #     self.buy_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
        pass

    def sell_even_and_open(self,
                           lots,
                           instrument=None,
                           price=None,
                           take_profit=None,
                           stop_loss=None,
                           trailing_stop=None):
        # logger.debug('self.first_open in strategy: {}'.format(self.first_open))
        # logger.debug('self.position[-1] in sell_even_and_open: {}'.format(self.position[-1]))
        # logger.debug('self.position[-2] in sell_even_and_open: {}'.format(self.position[-2]))
        # if first_open:  # 第一次开仓，只能卖出一次
        #     self.sell_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
        #     # self.first_open = False
        #     return
        # logger.debug('self.position[-1] in sell_even_and_open: {}'.format(self.position[-1]))
        # if self.position[-1] > 0:  # 只有当已建立多仓的情况下，才能卖出平仓并继续卖出开空仓
        #     self.sell_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
        #     self.sell_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
        pass

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

        lots = abs(self.position[-1])
        exit_all_order.execute(
            instrument=instrument,
            lots=lots,
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
                self._signal_list = [] if signal.lots == 0 else [signal]
                break
        for signal in self._signal_list:
            if signal.instrument is self.instrument:
                events.put(signal)

    def stop(self):
        pass

    def __process(self):
        """
        当数据不够给indicator生成信号时，会产生Warning，无交易发生
        当策略需要更多基本信息，比如10天内的平均仓位，则会产生IndexError，无交易发生，
        会一直更新新行情直到有足够的数据。
        """
        try:
            self.prenext()
            self.next()
        except Warning:
            date = str(self.market_event.cur_bar.cur_date)
            logger.debug('{} 信号不够，不发生交易'.format(date))
        except IndexError:
            date = str(self.market_event.cur_bar.cur_date)
            logger.debug('{} 数据不够，不发生交易'.format(date))

    def run_strategy(self):
        self.__start()
        self.__process()
        self.__prestop()
        self.stop()


class Strategy(StrategyBase):
    def __init__(self, market_event):
        super().__init__(market_event)
        position = self.position[-1]
        logger.info('position in strategy: {}'.format(position))

    def buy_even_and_open(self,
                          lots,
                          instrument=None,
                          price=None,
                          take_profit=None,
                          stop_loss=None,
                          trailing_stop=None):
        # first_open = self.first_open
        logger.debug('self.position[-1] in strategy: {}'.format(self.position[-1]))
        # if first_open:  # 第一次开仓，只能买入一次
        #     self.buy_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
        #     self.first_open = False
        #     return
        # logger.debug('self.position[-1] in buy_even_and_open: {}'.format(self.position))
        if self.position[-1] < 0:  # 只有当已建立空仓的情况下，才能买入平仓并继续买入开多仓
            # lots = lots * 2
            self.buy_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
            self.buy_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
        elif self.position[-1] == 0:
            self.buy_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)

    def sell_even_and_open(self,
                           lots,
                           instrument=None,
                           price=None,
                           take_profit=None,
                           stop_loss=None,
                           trailing_stop=None):
        # first_open = self.first_open
        logger.debug('self.position[-1] in sell_even_and_open: {}'.format(self.position[-1]))
        logger.debug('self.position[-2] in sell_even_and_open: {}'.format(self.position[-2]))
        # if first_open:  # 第一次开仓，只能卖出一次
        #     self.sell_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
        #     self.first_open = False
        #     return
        logger.debug('self.position[-1] in sell_even_and_open: {}'.format(self.position[-1]))
        if self.position[-1] > 0:  # 只有当已建立多仓的情况下，才能卖出平仓并继续卖出开空仓
            # lots = lots * 2
            self.sell_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
            self.sell_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
        elif self.position[-1] == 0:
            self.sell_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)

    def buy(self,
            lots,
            instrument=None,
            price=None,
            take_profit=None,
            stop_loss=None,
            trailing_stop=None):
        if self.position[-1] <= 0:  # 只有当未开仓或已建立空仓的情况才能买入
            logger.debug('self.position[-1] in buy: {}'.format(self.position[-1]))
            self.buy_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)

    def sell(self,
             lots,
             instrument=None,
             price=None,
             take_profit=None,
             stop_loss=None,
             trailing_stop=None):
        logger.debug('self.position[-1] in sell: {}'.format(self.position[-1]))
        if self.position[-1] >= 0:  # 只有当未开仓或已建立多仓的情况才能卖出
            self.sell_base(lots, instrument, price, take_profit, stop_loss, trailing_stop)
