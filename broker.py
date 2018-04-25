# coding:utf-8
from abc import ABC, abstractmethod
from event import events, FillEvent


class BrokerBase(ABC):
    """broker的基类"""

    def __init__(self):
        self.fill = None
        self.order_event = None
        self._notify = False

    @abstractmethod
    def submit_order(self):
        pass

    @abstractmethod
    def notify(self):
        pass

    @abstractmethod
    def change_status(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def prenext(self):
        pass

    @abstractmethod
    def next(self):
        pass

    @abstractmethod
    def check_before(self):
        pass

    @abstractmethod
    def check_after(self):
        pass

    def run_broker(self, order_event):
        self.order_event = order_event
        self.start()
        self.prenext()
        self.next()

    def set_notify(self):
        self._notify = True


class Broker(BrokerBase):
    """"""

    def __init__(self):
        super().__init__()

    def submit_order(self):
        """发送交易指令"""
        fill_event = FillEvent(self.order_event.order)
        events.put(fill_event)

    def check_before(self):
        """
        检查钱是否足够支持Order执行
        Return： True / False
        """
        execute_type = [
            'MARKET', 'LIMIT', 'STOP', 'CLOSE_ALL', 'STOP_LOSS_ORDER',
            'TAKE_PROFIT_ORDER', 'TRAILING_STOP_ORDER'
        ]
        oe = self.order_event
        return (
            self.fill.cash[-1] > oe.per_margin * oe.units * oe.price * oe.mult
            + self.fill.margin[-1] * oe.direction
            or oe.execute_type in execute_type)

    def check_after(self):
        """检查Order发送后是否执行成功"""
        return True

    def change_status(self, status):
        """
        改变订单状态
        Status = ["CREATED", "SUBMITTED", "ACCEPTED", "PARTIAL", "COMPLETED",
                  "CANCELLED", "EXPIRED", "MARGIN", "REJECTED",]
        """
        self.order_event.status = status

    def start(self):
        self.notify()
        if self.check_before():
            self.change_status('SUBMITTED')
            self.notify()
        else:
            print('现金不够，本次交易取消')

    def prenext(self):
        pass

    def next(self):
        """
        如果order执行类型为限价或停止，将状态改为PENDING（等待）；
        否则，状态改为FILLED（执行）；
        发送交易指令，发出通知
        """
        if self.check_before() and self.check_after():
            if self.order_event.execute_type in ['LIMIT', 'STOP']:
                self.change_status('PENDING')
            else:
                self.change_status('FILLED')
            self.submit_order()
            self.notify()

    def notify(self):
        if self._notify:
            print('{}, {}, {}, {} @ {}, units: {}, execute: {}'.format(
                self.order_event.date, self.order_event.instrument,
                self.order_event.order_type, self.order_event.status,
                self.order_event.price, self.order_event.units,
                self.order_event.execute_type))
