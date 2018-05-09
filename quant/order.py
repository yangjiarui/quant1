# coding:utf-8
from itertools import count
from quant.logging_backtest import logger


class OrderData(object):
    """处理Order数据，计算止盈、止损、追踪止损的价格"""

    def __init__(self, instrument, units, price, take_profit, stop_loss,
                 trailing_stop, cur_bar, execute_mode, order_type):
        self.units = units
        self.price = price
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop
        self.trailing_stop_calc = trailing_stop  # 作更新用
        self.instrument = instrument
        self._cur_bar = cur_bar
        self.execute_mode = execute_mode
        self.order_type = order_type
        self.execute_mode_price = None
        self.__set_order_info()

    def __set_order_info(self):
        """初始化各项数据"""
        self.__set_date()
        self.__set_direction()
        self.__set_price()
        self.__set_take_profit(self.price)
        self.__set_stop_loss(self.price)
        self.__set_trailing_stop()

    def __set_date(self):
        """设置时间，cur_bar_list中第一个date"""
        self.date = self._cur_bar.cur_date

    def __set_direction(self):
        """判断方向，买为1.0，卖为-1.0"""
        if self.order_type is 'BUY':
            self.direction = 1.0
        elif self.order_type is 'SELL':
            self.direction = -1.0

    def __set_price(self):
        """
        根据execute_mode即开仓平仓，计算价格
        更改结算价为当条bar的收盘价
        """
        logger.info('self.execute_mode: {}'.format(self.execute_mode))
        if self.execute_mode is 'open':
            # self.execute_mode_price = self._cur_bar.next_open
            self.execute_mode_price = self._cur_bar.cur_close
        elif self.execute_mode is 'close':
            self.execute_mode_price = self._cur_bar.cur_close

        logger.info('self.price: {}'.format(self.price))
        if self.price in ['open', 'close', None]:
            self.price = self.execute_mode_price
        elif type(self.price) is type:
            if self.price.type is 'points':
                self.price = self.price.points + self.execute_mode_price
            elif self.price.type is 'pct':
                self.price = self.execute_mode_price * self.price.pct  # ???
            else:
                raise SyntaxError('价格必须为点数或百分数!')
        logger.info('self.price: {}'.format(self.price))

    def __set_take_profit(self, cur_price):
        """计算止盈价格"""
        if self.take_profit:
            if self.take_profit.type is 'points':
                if self.take_profit.points < 0:
                    raise SyntaxError('止盈中的点数必须大于0！')
                points = self.take_profit.points * self.direction
                self.take_profit = cur_price + points
            elif self.take_profit.type is 'pct':
                if self.take_profit.pct < 0:
                    raise SyntaxError('止盈中的百分比必须大于0！')
                pct = 1 + self.take_profit.pct * self.direction
                self.take_profit = cur_price * pct
            else:
                raise SyntaxError('止盈必须设置点数或百分比！')

    def __set_stop_loss(self, cur_price):
        """计算止损价格"""
        if self.stop_loss:
            if self.stop_loss.type is 'points':
                if self.stop_loss.points < 0:
                    raise SyntaxError('止损中的点数必须大于0！')
                points = self.stop_loss.points * self.direction
                self.stop_loss = cur_price - points
            elif self.stop_loss.type is 'pct':
                if self.stop_loss.pct < 0:
                    raise SyntaxError('止损中的百分比必须大于0！')
                pct = 1 - self.stop_loss.pct * self.direction
                self.stop_loss = cur_price * pct
            else:
                raise SyntaxError('止损必须设置点数或百分比！')

    def __set_trailing_stop(self):
        """计算追踪止损价格"""
        if self.trailing_stop_calc:
            if self.trailing_stop_calc.type is 'points':
                if self.trailing_stop_calc.points < 0:
                    raise SyntaxError('追踪止损中的点数必须大于0！')
                points = self.trailing_stop_calc.points * self.direction
                self.trailing_stop = self.price - points
            elif self.trailing_stop_calc.type is 'pct':
                if self.trailing_stop_calc.pct < 0:
                    raise SyntaxError('追踪止损中的百分比必须大于0！')
                pct = 1 - self.trailing_stop_calc.pct * self.direction
                self.trailing_stop = self.price * pct
            else:
                raise SyntaxError('追踪止损必须设置点数或百分比！')


class OrderBase(object):
    """
    execute_type = ['MARKET', 'LIMIT', 'STOP','CLOSE_ALL','STOP_LOSS_ORDER',
                     'TAKE_PROFIT_ORDER', 'TRAILING_STOP_ORDER']
    order_type = ['BUY', 'SELL']
    status = ['CREATED', ]
    """

    unique_id = count(1)

    def __init__(self, market_event):
        self.order_ID = next(self.unique_id)  # 从1开始，每次迭代，id+1
        self.set_status("CREATED")
        self._parent = None

        # 从market_event获取基本属性
        self._instrument = market_event.instrument
        self._cur_bar = market_event.cur_bar
        self._execute_mode = market_event.execute_mode
        self._per_comm = market_event.per_comm
        self._per_margin = market_event.per_margin
        self._mult = market_event.mult
        self._feed = market_event.feed

        # 在子类中被初始化的部分
        self._order_data = None
        self._date = None
        self._units = None
        self._price = None
        self._take_profit = None
        self._stop_loss = None
        self._execute_type = None
        self._direction = None
        self._trailing_stop = None
        self.trailing_stop_calc = None

    @property
    def order_id(self):
        return self.order_ID

    # @order_id.setter
    # def order_id(self, value):
    #     self.order_id = value

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value

    @property
    def parent(self):
        return self._parent

    @property
    def instrument(self):
        return self._instrument

    @property
    def per_comm(self):
        return self._per_comm

    @property
    def per_margin(self):
        return self._per_margin

    @property
    def mult(self):
        return self._mult

    @property
    def feed(self):
        return self._feed

    @property
    def order_type(self):
        return self._order_type

    @property
    def date(self):
        return self._date

    @property
    def units(self):
        return self._units

    @property
    def price(self):
        return self._price

    @property
    def take_profit(self):
        return self._take_profit

    @property
    def stop_loss(self):
        return self._stop_loss

    @property
    def execute_type(self):
        return self._execute_type

    @property
    def direction(self):
        return self._direction

    @property
    def trailing_stop(self):
        return self._trailing_stop

    def set_status(self, status):
        self._status = status

    def set_parent(self, parent):
        self._parent = parent

    def set_per_comm(self, per_comm):
        self._per_comm = per_comm

    # 先设定指令类型，再判断执行（set_order_type -> execute）
    def set_order_type(self, order_type):
        self._order_type = order_type
        self._direction = 1.0 if order_type == "BUY" else -1.0

    def set_date(self, date):
        self._date = date

    def set_units(self, units):
        self._units = units

    def set_price(self, price):
        self._price = price

    def set_take_profit(self, price):
        self._take_profit = price

    def set_stop_loss(self, price):
        self._stop_loss = price

    def set_execute_type(self, execute_type):
        self._execute_type = execute_type

    def set_trailing_stop(self, price):
        self._trailing_stop = price


class Order(OrderBase):
    def execute(self, instrument, units, price, take_profit, stop_loss,
                trailing_stop):
        """执行"""
        if instrument is None:
            instrument = self._instrument

        self._order_data = OrderData(
            instrument=instrument,
            units=units,
            price=price,
            take_profit=take_profit,
            stop_loss=stop_loss,
            trailing_stop=trailing_stop,
            cur_bar=self._cur_bar,
            execute_mode=self._execute_mode,
            order_type=self.order_type)
        self.__set_order_data()

    def __set_order_data(self):
        """初始化各项基本信息,并判断指令种类execute_type"""
        self._instrument = self._order_data.instrument
        self._direction = self._order_data.direction
        self._date = self._order_data.date
        self._units = self._order_data.units
        self._price = self._order_data.price
        logger.info('self._price: {}'.format(self._price))
        self._take_profit = self._order_data.take_profit
        self._stop_loss = self._order_data.stop_loss
        self._trailing_stop = self._order_data.trailing_stop
        self._trailing_stop_calc = self._order_data.trailing_stop_calc

        execute_mode_price = self._order_data.execute_mode_price
        logger.info('execute_mode_price: {}'.format(execute_mode_price))
        if self._execute_type == 'CLOSE_ALL':
            return
        elif self._price > execute_mode_price:
            self._execute_type = 'STOP' if self._order_type == 'BUY' else 'LIMIT'
        elif self._price < execute_mode_price:
            self._execute_type = 'LIMIT' if self._order_type == 'BUY' else 'STOP'
        elif self._price == execute_mode_price:
            self._execute_type = 'MARKET'

    def __get_trailing_price(self, new, old):
        """根据多空决定追踪止损取值"""
        if self._order_type == 'BUY':
            return max(new, old)
        elif self._order_type == 'SELL':
            return min(new, old)

    def update_trailing_stop(self, cur_price):
        """根据价格更新追踪止损具体价格"""
        if self._trailing_stop_calc:
            if self._trailing_stop_calc.type == 'points':
                points = self._trailing_stop_calc.points * self._direction
                new = cur_price - points
                old = self.trailing_stop
                self._trailing_stop = self.__get_trailing_price(new, old)
            elif self._trailing_stop_calc.type == 'pct':
                pct = 1 - self._trailing_stop_calc * self._direction
                new = cur_price * pct
                old = self._trailing_stop
                self._trailing_stop = self.__get_trailing_price(new, old)
            else:
                raise SyntaxError('追踪止损必须设置点数或百分比！')


class BuyOrder(Order):
    _order_type = 'BUY'


class SellOrder(Order):
    _order_type = 'SELL'


class ExitAllOrder(Order):
    _order_type = None

    def __init__(self, market_event):
        super().__init__(market_event)
        self._execute_type = 'CLOSE_ALL'
