# coding:utf-8
from quant import dataseries
from copy import copy
from quant.event import events
from quant.logging_backtest import logger


class FillBase(object):
    """回测执行模块的基类"""
    def __init__(self):
        # 设置默认初始资金，如果用户不更改，则用这个资金进行回测
        self.initial_cash = 100000

        self.position = dataseries.PositionSeries()  # 仓位
        self.margin = dataseries.MarginSeries()  # 保证金
        self.avg_price = dataseries.AvgPriceSeries()  # 均价
        self.commission = dataseries.CommissionSeries()  # 手续费
        self.cash = dataseries.CashSeries()  # 现金
        # 平仓盈亏
        self.realized_gain_and_loss = dataseries.RealizedGainAndLossSeries()
        # 浮动盈亏
        self.unrealized_gain_and_loss = dataseries.UnrealizedGainAndLossSeries()
        self.balance = dataseries.BalanceSeries()  # 余额

        self._order_list = []
        self._trade_list = []
        self._completed_list = []

    @property
    def completed_list(self):
        return self._completed_list

    def set_cash(self, cash):
        self.initial_cash = cash  # 重设初始资金

    def set_dataseries_instrument(self, instrument):
        self.position.set_instrument(instrument)
        self.margin.set_instrument(instrument)
        self.commission.set_instrument(instrument)
        self.avg_price.set_instrument(instrument)
        self.realized_gain_and_loss.set_instrument(instrument)
        self.unrealized_gain_and_loss.set_instrument(instrument)

    def update_time_index(self, feed_list):
        pass

    def check_trade_list(self, feed):
        pass

    def check_order_list(self, feed):
        pass

    def run_fill(self, fill_event):
        pass


class BacktestFill(FillBase):
    """回测执行模块，更新仓位、保证金、均价、手续费、平仓盈亏、浮动盈亏等信息"""

    def update_position(self, fill_event):
        """
        更新仓位
        如果最后一个仓位的执行类型为LIMIT或STOP，仓位不变，更新时间；
        否则，仓位更新，加上变更量，并更新时间
        """
        last_position = self.position[-1]
        if fill_event.execute_type in ['LIMIT', 'STOP']:
            position = last_position
        else:
            position = last_position + fill_event.units * fill_event.direction
        self.position.add(fill_event.date, position)

    def update_margin(self, fill_event):
        """
        更新保证金
        根据position确定，多头时保证金为正，空头时保证金为负
        暂时只考虑了期货
        """
        margin = self.margin[-1]
        cur_position = self.position[-1]
        if fill_event.execute_type in ['LIMIT', 'STOP']:
            pass
        else:
            cur_close = fill_event.price
            margin = fill_event.per_margin * (
                cur_position * fill_event.mult * cur_close)
        self.margin.add(fill_event.date, margin)

    def update_commission(self, fill_event):
        """
        更新手续费，手续费 = 成交额 × 手续费比例
        """
        commission = self.commission[-1]
        per_comm = fill_event.per_comm

        if fill_event.execute_type in ['LIMIT', 'STOP']:
            pass
        else:
            per_comm *= fill_event.mult
            commission += fill_event.units * fill_event.price * per_comm
        self.commission.add(fill_event.date, commission)

    def update_avg_price(self, fill_event):
        """
        更新均价
        """
        f = fill_event
        avg_price = self.avg_price[-1]
        last = self.position[-2]  # 上一个仓位
        cur = self.position[-1]  # 刚刚更新的仓位

        if cur == 0:  # 平仓了，
            avg_price = 0
        else:  # 未平仓
            if f.execute_type in ['LIMIT', 'STOP']:
                pass
            # 上一次仓位为0，本次开仓，均价即为本次执行价
            elif last == 0:
                avg_price = f.price
            # 上一次仓位为多头，即买入了仓位，当最新仓位仍为多头时，均价 = 总成交额 / 最新仓位
            # 当最新仓位为负时，即卖出平仓后又卖出开仓了，均价即为卖出的执行价
            elif last > 0:
                if f.order_type == 'BUY':
                    avg_price = (last * avg_price + f.units * f.price) / cur
                if f.order_type == 'SELL':
                    if cur > 0:
                        avg_price = (last * avg_price - f.units * f.price) / cur
                    elif cur < 0:
                        avg_price = f.price
            # 上一次仓位为空头时，当最新仓位变为多头时，即买入平仓后又买入开仓了，
            # 均价即为买入的执行价；否则，均价 = 总成交额 / 最新仓位
            elif last < 0:
                if f.order_type == 'BUY':
                    if cur > 0:
                        avg_price = f.price
                    elif cur < 0:
                        avg_price = (-last * avg_price - f.units * f.price) / cur
                elif f.order_type == 'SELL':
                    avg_price = (-last * avg_price + f.units * f.price) / cur
        self.avg_price.add(f.date, abs(avg_price))

    def update_unrealized_gain_and_loss(self, fill_event):
        """
        更新浮动盈亏，浮动盈亏 = （现价 - 现均价） × 现仓位 × 杠杆
        """
        cur_position = self.position[-1]
        cur_avg = self.avg_price[-1]
        cur_close = fill_event.feed.cur_bar.cur_close
        cur_high = fill_event.feed.cur_bar.cur_high
        cur_low = fill_event.feed.cur_bar.cur_low

        if cur_avg == 0:
            unrealized_G_L = unrealized_G_L_high = unrealized_G_L_low = 0
        else:
            diff = cur_close - cur_avg
            diff_h = cur_high - cur_avg
            diff_l = cur_low - cur_avg
            unrealized_G_L = diff * cur_position * fill_event.mult
            unrealized_G_L_high = diff_h * cur_position * fill_event.mult
            unrealized_G_L_low = diff_l * cur_position * fill_event.mult
        self.unrealized_gain_and_loss.add(
            fill_event.date,
            unrealized_G_L,
            unrealized_G_L_high,
            unrealized_G_L_low
            )

    def update_balance(self, fill_event):
        """
        更新资产余额
        """
        total_re_profit = sum(self.realized_gain_and_loss.list)
        total_profit = total_re_profit + self.unrealized_gain_and_loss.total()
        total_profit_high = total_re_profit + self.unrealized_gain_and_loss.total_high()
        total_profit_low = total_re_profit + self.unrealized_gain_and_loss.total_low()
        total_commission = self.commission.total()

        balance = self.initial_cash + total_profit - total_commission
        balance_high = self.initial_cash + total_profit_high - total_commission
        balance_low = self.initial_cash + total_profit_low - total_commission

        self.balance.add(fill_event.date, balance, balance_high, balance_low)

    def update_cash(self, fill_event):
        """
        更新现金，现金 = 资产余额 - 本次已缴纳的保证金
        """
        cur_balance = self.balance[-1]
        total_margin = self.margin.total()
        cash = cur_balance - total_margin
        self.cash.add(fill_event.date, cash)

    def update_info(self, fill_event):
        """
        更新基本信息，更新信息后，删除重复的信息
        第一笔交易会删除update_time_index产生的初始化信息
        第二笔交易开始删除前一笔交易，慢慢迭代，最终剩下最后一笔交易获得的信息
        """
        self.update_position(fill_event)
        self.update_margin(fill_event)
        self.update_commission(fill_event)
        self.update_avg_price(fill_event)
        self.update_unrealized_gain_and_loss(fill_event)
        self.update_balance(fill_event)
        self.update_cash(fill_event)

        self.position.del_last()
        self.margin.del_last()
        self.commission.del_last()
        self.avg_price.del_last()
        self.unrealized_gain_and_loss.del_last()
        self.balance.del_last()
        self.cash.del_last()

    def update_time_index(self, feed_list):
        """
        保持每日开盘后的数据更新
        """
        date = feed_list[-1].cur_bar.cur_date
        logger.info('date: {}'.format(date))

        for feed in feed_list:
            # 控制计算的价格，同指令成交价一样
            price = feed.cur_bar.cur_close
            high = feed.cur_bar.cur_high
            low = feed.cur_bar.cur_low

            self.set_dataseries_instrument(feed.instrument)
            self.position.copy_last(date)  # 更新仓位

            # 更新保证金
            margin = self.position[-1] * price * feed.per_margin * feed.mult
            self.margin.add(date, margin)
            # 更新平均价格
            self.avg_price.copy_last(date)
            # 更新手续费，注意期货手续费需要重新计算，还未计算
            self.commission.copy_last(date)
            # 更新浮动盈亏
            cur_avg = self.avg_price[-1]
            cur_position = self.position[-1]
            unrealized_G_L = (price - cur_avg) * cur_position * feed.mult
            unrealized_G_L_high = (high - cur_avg) * cur_position * feed.mult
            unrealized_G_L_low = (low - cur_avg) * cur_position * feed.mult
            if self.avg_price[-1] == 0:
                unrealized_G_L = unrealized_G_L_high = unrealized_G_L_low = 0
            self.unrealized_gain_and_loss.add(
                date,
                unrealized_G_L,
                unrealized_G_L_high,
                unrealized_G_L_low
                )

        # 更新balance
        commission = self.commission[-1]
        total_re_profit = sum(self.realized_gain_and_loss.list)
        total_profit = total_re_profit + self.unrealized_gain_and_loss.total()
        total_profit_high = (
            total_re_profit + self.unrealized_gain_and_loss.total_high())
        total_profit_low = (
            total_re_profit + self.unrealized_gain_and_loss.total_low())

        balance = self.initial_cash + total_profit - commission
        balance_high = self.initial_cash + total_profit_high - commission
        balance_low = self.initial_cash + total_profit_low - commission

        self.balance.add(date, balance, balance_high, balance_low)

        # 更新cash
        total_margin = self.margin.total()
        cash = self.balance[-1] - total_margin
        logger.info('cash: {}'.format(cash))
        logger.info('date for cash: {}'.format(date))
        self.cash.add(date, cash)
        logger.info(222222)

        # 检查是否爆仓
        if self.balance[-1] <= 0 or self.cash[-1] <= 0:
            for feed in feed_list:
                feed.continue_backtest = False
            logger.info('警告：策略已造成爆仓！')

    def _update_trade_list(self, fill_event):
        """
        根据具体交易情况更新交易列表trade_list
        情况一：做多，若有空单，将空单逐个抵消，判断：
                            若抵消后还有剩余多单，则多开一个多单
                            若无剩余多单，则修改原空单为多单
        情况二：做空，若有多单，将多单逐个抵消，判断：
                            若抵消后还有剩余空单，则多开一个空单
                            若无剩余空单，则修改原多单为空单
        情况三：全部平仓，若有单，将空单和多单全部抵消
        情况四：触发止盈、止损、移动止损，对应的单相互抵消
        """
        f = fill_event
        try:
            last_position = self.position[-2]  # 上一个仓位
        except IndexError:
            last_position = 0
        # 情况四中不同种类的单
        extra_list = [
            'TAKE_PROFIT_ORDER', 'STOP_LOSS_ORDER', 'TRAILING_STOP_ORDER']

        def get_re_profit(trade_units):
            re_profit = (f.price - i.price) * trade_units * f.mult * i.direction
            self.realized_gain_and_loss.add(f.date, re_profit)

            if self.realized_gain_and_loss.date[-2] is f.date:
                new_realized_g_l = (
                    self.realized_gain_and_loss[-1] + self.realized_gain_and_loss[-2])
                self.realized_gain_and_loss.update_cur(new_realized_g_l)
                self.realized_gain_and_loss.del_last()

        # 首先判断是否有情况四发生，即止盈、止损、移动止损
        if f.execute_type in extra_list:
            for i in self._trade_list:
                if f.order.parent is i:  # 找到父类，删除原空单，计算利润
                    self._trade_list.remove(i)
                    self._completed_list.append((copy(i), copy(f)))
                    f.units = 0

        else:
            # 判断情况一，即做多的情况
            if f.order_type == 'BUY' and last_position < 0:
                for i in self._trade_list:
                    # 剩余空单且品种相同
                    if f.instrument is i.instrument and i.order_type == 'SELL':
                        if f.units == 0:
                            break
                        if i.units > f.units:  # 空单大于多单，剩余空单
                            index_i = self._trade_list.index(i)
                            self._trade_list.pop(index_i)  # 删除原空单
                            self._completed_list.append((copy(i), copy(f)))
                            i.units -= f.units  # 修改抵消后剩余的空单
                            get_re_profit(f.units)  # 用执行交易的部分计算利润
                            f.units = 0  # 没有多单了，单位设为0

                            if i.units != 0:
                                # 修改后的单子放回原位
                                self._trade_list.insert(index_i, i)

                        elif i.units <= f.units:  # 空单小于多单，抵消后删除空单
                            self._trade_list.remove(i)
                            self._completed_list.append((copy(i), copy(f)))
                            get_re_profit(i.units)  # 用执行交易的部分计算利润
                            f.units -= i.units  # 修改多单仓位，若为0，后面会删除

            # 判断情况二，即做空的情况
            elif f.order_type == 'SELL' and last_position > 0:
                for i in self._trade_list:
                    # 剩余多单且品种相同
                    if f.instrument is i.instrument and i.order_type == 'BUY':
                        if f.units == 0:
                            break
                        if i.units > f.units:  # 多单大于空单，剩余多单
                            index_i = self._trade_list.index(i)
                            self._trade_list.pop(index_i)  # 删除原多单
                            self._completed_list.append((copy(i), copy(f)))
                            i.units -= f.units  # 修改抵消后剩余的多单
                            get_re_profit(f.units)  # 用执行交易的部分计算利润
                            f.units = 0  # 没有空单了，单位设为0

                            if i.units != 0:
                                # 修改后的单子放回原位
                                self._trade_list.insert(index_i, i)

                        elif i.units <= f.units:  # 多单小于空单，抵消后删除多单
                            self._trade_list.remove(i)
                            self._completed_list.append((copy(i), copy(f)))
                            get_re_profit(i.units)  # 用执行交易的部分计算利润
                            f.units -= i.units  # 修改空单仓位，若为0，后面会删除

    def __to_list(self, fill_event):
        """
        根据情况将order放入trade_list或order_list
        """
        if fill_event.execute_type in ['LIMIT', 'STOP']:
            self._order_list.append(fill_event)

        else:
            self._update_trade_list(fill_event)
            if fill_event.units != 0:
                self._trade_list.append(fill_event)

    def run_fill(self, fill_event):
        """每次指令发过来后，先直接记录下来，然后再去对冲仓位"""
        self.set_dataseries_instrument(fill_event.instrument)
        self.update_info(fill_event)
        self.__to_list(fill_event)

    def check_trade_list(self, feed):
        """
        存在漏洞，先判断的止盈止损，后判断移动止损
        每次触发止盈止损后，发送一个相反的指令，并且自己对冲掉自己
        因为假设有10个多单，5个止损，5个没止损，若止损时对冲5个没止损的单，则会产生错误
        这种情况只会出现在同时多个Buy或者Sell，且有不同的stop或者limit
        所以给多一个dad属性，用于回去寻找自己以便对冲自己
        """

        def set_take_stop(trade):
            """止盈止损设定函数，一旦触发止盈止损，则BUY变为SELL，SELL变为BUY"""
            trade.type = 'Order'
            if trade.order_type == 'BUY':
                trade.order_type = 'SELL'
            else:
                trade.order_type = 'BUY'
            trade.take_profit = None
            trade.stop_loss = None
            trade.trailing_stop = None
            trade.date = data_today['date']
            events.put(trade)

        data_today = feed.cur_bar.cur_data  # 今日的价格
        # 以这个价格计算移动止损
        cur_price = data_today[feed.trailing_stop_execute_mode]

        # 检查止盈止损，触发交易
        for trade in self._trade_list:
            i = copy(trade)  # 必须要复制，不然会修改掉原来的订单
            i.order = copy(trade.order)
            i.order.set_parent(trade)  # 等下要回去原来的列表里面找父类

            if i.instrument != feed.instrument:
                continue  # 不是同个instrument无法比较，所以跳过
            if i.take_profit is i.stop_loss is i.trailing_stop:
                continue  # 没有止盈止损，所以跳过
            if trade.date is data_today['date']:
                continue  # 防止当天挂的单，因为昨天的价格而成交，不符合逻辑

            # 检查移动止损,修改止损价格
            if i.trailing_stop:
                i.order.update_trailing_stop(cur_price)
                i.trailing_stop = i.order.trailing_stop

            # 根据指令判断，设置买或卖
            try:
                if i.execute_type in ['LIMIT', 'STOP']:
                    continue

                if i.take_profit and i.stop_loss:
                    if (data_today['low'] < i.take_profit < data_today['high']
                            and data_today['low'] < i.stop_loss < data_today['high']):
                        logger.info('注意：止盈止损出现矛盾，已选择止损')
                        i.execute_type = 'STOP_LOSS_ORDER'
                        i.price = i.stop_loss
                        set_take_stop(i)
                        continue
                if i.take_profit:
                    # 只有止盈，止盈价在最高价最低价之间或者
                    # 当order_type为买入时，止盈价小于最低价或者
                    # 当order_type为卖出时，止盈价大于最高价时    执行止盈
                    if (data_today['low'] < i.take_profit < data_today['high']
                        or (i.take_profit < data_today['low']
                            if i.order_type == 'BUY' else False)
                        or (i.take_profit > data_today['high']
                            if i.order_type == 'SELL' else False)):
                        i.execute_type = 'TAKE_PROFIT_ORDER'
                        i.price = i.take_profit
                        set_take_stop(i)
                        continue
                if i.stop_loss:
                    # 只有止损，止损价在最高价最低价之间或者
                    # 当order_type为买入时，止损价小于最高价或者
                    # 当order_type为卖出时，止损价大于最低价时    执行止损
                    if (data_today['low'] < i.stop_loss < data_today['high']
                        or (i.stop_loss < data_today['high']
                            if i.order_type == 'BUY' else False)
                        or (i.stop_loss > data_today['low']
                            if i.order_type == 'SELL' else False)):
                        i.execute_type = 'STOP_LOSS_ORDER'
                        i.price = i.stop_loss
                        set_take_stop(i)
                        continue
                if i.trailing_stop:
                    # 移动止损，移动止损价在最高价最低价之间或者
                    # 当order_type为买入时，移动止损价大于最高价或者
                    # 当order_type为卖出时，移动止损价小于最低价时    执行移动止损
                    if (data_today['low'] < i.trailing_stop < data_today['high']
                        or (i.trailing_stop > data_today['high']
                            if i.order_type == 'BUY' else False)
                        or (i.trailing_stop < data_today['low']
                            if i.order_type == 'SELL' else False)):
                        i.execute_type = 'TRAILING_STOP_ORDER'
                        i.price = i.trailing_stop
                        set_take_stop(i)
                        continue
            except:
                raise SyntaxError('判断止盈止损部分有语法错误！')

    def check_order_list(self, feed):
        """检查挂单是否触发"""
        data_today = feed.cur_bar.cur_data

        def set_event(order_type, order, change_price=True):
            self._order_list.remove(order)
            if change_price:
                order.price = data_today['open']
            order.type = 'Order'
            order.order_type = order_type
            order.date = data_today['date']
            order.execute_type = f'{order.execute_type} Triggered'
            events.put(order)

        for i in self._order_list:
            if i.instrument != feed.instrument:
                continue  # 不是同个instrument无法比较，所以跳过

            # 多单挂单
            if i.order_type == 'BUY':
                # 执行方式为停损，且开盘价大于定价，则以开盘价买入
                if i.execute_type == 'STOP' and data_today['open'] > i.price:
                    set_event('BUY', i)
                # 执行方式为限价，且开盘价小于定价，则以开盘价买入
                if i.execute_type == 'LIMIT' and data_today['open'] < i.price:
                    set_event('BUY', i)
                # 定价在最低价和最高价之间，以原定价买入
                elif data_today['low'] < i.price < data_today['high']:
                    set_event('BUY', i, False)

            # 空单挂单
            if i.order_type == 'SELL':
                # 执行方式为限价，且开盘价大于定价，则以开盘价卖出
                if i.execute_type == 'LIMIT' and data_today['open'] > i.price:
                    set_event('SELL', i)
                # 执行方式为停损，且开盘价小于定价，则以开盘价卖出
                elif i.execute_type == 'STOP' and data_today['open'] < i.price:
                    set_event('SELL', i)
                # 定价在最低价和最高价之间，以原定价买入
                elif data_today['low'] < i.price < data_today['high']:
                    set_event('SELL', i, False)
