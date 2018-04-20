# coding:utf-8
import dataseries


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

    @property
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
        cur_high = fill_event.cur_bar.cur_high
        cur_low = fill_event.cur_bar.cur_low

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

        for feed in feed_list:
            # 控制计算的价格，同指令成交价一样
            price = feed.cur_bar.cur_close
            high = feed.cur_bar.cur_high
            low = feed.cur_bar.cur_low

            self.set_dataseries_instrument(feed.instrument)
            self.position.copy_last(date)  # 更新仓位

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
        total_profit_high = total_re_profit + self.unrealized_gain_and_loss.total_high()
        total_profit_low = total_re_profit + self.unrealized_gain_and_loss.total_low()

        balance = self.initial_cash + total_profit - commission
        balance_high = self.initial_cash + total_profit_high - commission
        balance_low = self.initial_cash + total_profit_low - commission

        self.balance.add(date, balance, balance_high, balance_low)

        # 更新cash
        total_margin = self.margin.total()
        cash = self.balance[-1] - total_margin
        self.cash.add(date, cash)

        # 检查是否爆仓
        if self.balance[-1] <= 0 or self.cash[-1] <= 0:
            for feed in feed_list:
                feed.continue_backtest = False
            print('警告：策略已造成爆仓！')

    def _update_trade_list(self, fill_event):
        """
        根据具体交易情况更新交易列表trade_list
        """
