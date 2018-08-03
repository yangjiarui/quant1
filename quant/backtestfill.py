# coding:utf-8
from quant import dataseries
from copy import copy
from quant.event import events
from quant.logging_backtest import logger
import numpy as np


class FillBase(object):
    """回测记录模块的基类"""
    def __init__(self):
        # 设置默认初始资金，如果用户不更改，则用这个资金进行回测
        self.initial_cash = 100000

        self.position = dataseries.PositionSeries()  # 仓位
        self.margin = dataseries.MarginSeries()  # 保证金
        self.avg_price = dataseries.AvgPriceSeries()  # 均价
        self.commission = dataseries.CommissionSeries()  # 手续费
        self.long_commission = dataseries.LongCommissionSeries()  # 多头手续费
        self.short_commission = dataseries.ShortCommissionSeries()  # 空头手续费
        self.cash = dataseries.CashSeries()  # 现金
        # 平仓盈亏
        self.realized_gain_and_loss = dataseries.RealizedGainAndLossSeries()
        self.long_realized_gain_and_loss = dataseries.LongRealizedGainAndLossSeries()
        self.short_realized_gain_and_loss = dataseries.ShortRealizedGainAndLossSeries()
        logger.debug('realized_gain_and_loss in init: {}'.format(self.realized_gain_and_loss))
        # 浮动盈亏
        self.unrealized_gain_and_loss = dataseries.UnrealizedGainAndLossSeries()
        self.equity = dataseries.EquitySeries()  # 余额

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
        self.long_commission.set_instrument(instrument)
        self.short_commission.set_instrument(instrument)
        self.avg_price.set_instrument(instrument)
        self.realized_gain_and_loss.set_instrument(instrument)
        self.long_realized_gain_and_loss.set_instrument(instrument)
        self.short_realized_gain_and_loss.set_instrument(instrument)
        logger.debug('realized_gain_and_loss in set_dataseries_instrument: {}'.format(self.realized_gain_and_loss.list))
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
    """回测记录模块，更新仓位、保证金、均价、手续费、平仓盈亏、浮动盈亏等信息"""

    def __init__(self):
        super().__init__()
        self.first_open = True
        # self.units = fill_event.units

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
            position = int(last_position + fill_event.lots * fill_event.direction)
        logger.info('position in date: {} {}'.format(position, fill_event.date))
        self.position.add(fill_event.date, position)

    def update_margin(self, fill_event):
        """
        更新保证金
        根据position确定，多头时保证金为正，空头时保证金为负
        暂时只考虑了期货，以当条bar的收盘价为当日结算价
        当日交易保证金 = 持仓均价 × 当日结束交易后的持仓总量 × 交易保证金比例
        """
        margin = 0
        cur_position = self.position[-1]
        avg_price = self.avg_price[-1]
        if fill_event.execute_type in ['LIMIT', 'STOP']:
            pass
        else:
            cur_close = fill_event.price
            logger.info('cur_close 结算价 in date：{} in {}'.format(cur_close, fill_event.date))
            logger.info('fill_event.execute_type in date：{} in {}'.format(fill_event.execute_type, fill_event.date))
            # margin = fill_event.per_margin * (
            #     cur_position * fill_event.mult * cur_close)
            logger.info('fill_event.per_margin * cur_position * avg_price * fill_event.units: {}, {}, {}, {}'.format(
                fill_event.per_margin, cur_position, avg_price, fill_event.units))
            # 保证金不能为负，用持仓均价计算，不用当日结算价计算，保留两位小数
            margin = np.round(fill_event.per_margin * fill_event.units * avg_price * fill_event.lots, 2)
        logger.info('margin in date: {} {}'.format(margin, fill_event.date))
        self.margin.add(fill_event.date, margin)

    def update_commission(self, fill_event):
        """
        更新手续费，手续费 = 成交额 × 手续费比例
        """
        commission = 0  # 不交易就没有手续费
        per_comm = fill_event.per_comm
        logger.info('---slippage in update_commission---:{}'.format(fill_event.slippage))

        if fill_event.execute_type in ['LIMIT', 'STOP']:
            pass
        elif fill_event.order_type in ['SELL', 'BUY']:
            # per_comm *= fill_event.mult
            # 保留两位小数
            commission = np.round(fill_event.units * fill_event.price * per_comm * fill_event.lots, 2)
            logger.debug('commission {}'.format(commission))
            logger.debug('fill_event.units {}'.format(fill_event.units))
            logger.debug('fill_event.price in update_commission: {}'.format(fill_event.price))
            logger.debug('per_comm in update_commission: {}'.format(per_comm))
        logger.debug('commission in date in update_commission: {} {}'.format(commission, fill_event.date))
        logger.debug('commission.total in date in update_commission: {} {}'.format(commission, fill_event.date))
        self.commission.add(fill_event.date, commission)

    def update_avg_price(self, fill_event):
        """
        更新均价
        """
        avg_price = self.avg_price[-1]
        last = self.position[-2]  # 上一个仓位
        cur = self.position[-1]  # 刚刚更新的仓位

        if cur == 0:  # 平仓了，
            avg_price = 0
        else:  # 未平仓
            if fill_event.execute_type in ['LIMIT', 'STOP']:
                pass
            # 上一次仓位为0，本次开仓，均价即为本次执行价
            elif last == 0:
                avg_price = fill_event.price
            # 上一次仓位为多头，即买入了仓位，当最新仓位仍为多头时，均价 = 总成交额 / 最新仓位
            # 当最新仓位为负时，即卖出平仓后又卖出开仓了，均价即为卖出的执行价
            elif last > 0:
                if fill_event.order_type == 'BUY':
                    avg_price = (last * avg_price + fill_event.units * fill_event.price) / cur
                if fill_event.order_type == 'SELL':
                    if cur > 0:
                        avg_price = (last * avg_price - fill_event.units * fill_event.price) / cur
                    elif cur < 0:
                        avg_price = fill_event.price
            # 上一次仓位为空头时，当最新仓位变为多头时，即买入平仓后又买入开仓了，
            # 均价即为买入的执行价；否则，均价 = 总成交额 / 最新仓位
            elif last < 0:
                if fill_event.order_type == 'BUY':
                    if cur > 0:
                        avg_price = fill_event.price
                    elif cur < 0:
                        avg_price = (-last * avg_price - fill_event.units * fill_event.price) / cur
                elif fill_event.order_type == 'SELL':
                    avg_price = (-last * avg_price + fill_event.units * fill_event.price) / cur
        logger.debug('avg_price in date in update_avg_price: {} {}'.format(avg_price, fill_event.date))
        self.avg_price.add(fill_event.date, avg_price)

    def update_unrealized_gain_and_loss(self, fill_event):
        """
        更新浮动盈亏，浮动盈亏 = （现价 - 现均价） × 现仓位 × 单位（300）
        # 更新浮动盈亏，单位默认为300
        # 买入开仓时，浮动盈亏 = （结算价 - 买入价）× 单位 × 手数
        # 卖出开仓时，浮动盈亏 = （卖出价 - 结算价）× 单位 × 手数
        """
        cur_position = self.position[-1]
        cur_avg = self.avg_price[-1]
        cur_close = fill_event.feed.cur_bar.cur_close
        unrealized_g_l = 0

        if cur_avg == 0:
            unrealized_g_l = 0
        else:
            diff = cur_close - cur_avg
            # 保留两位小数
            unrealized_g_l = np.round(diff * cur_position * fill_event.units, 2)
            if not unrealized_g_l:  # 0.0, -0.0, 0 等情况，取整
                unrealized_g_l = int(unrealized_g_l)

        self.unrealized_gain_and_loss.add(
            fill_event.date,
            unrealized_g_l,
        )

    def update_equity(self, fill_event):
        """
        更新资产余额
        """
        equity = self.equity[-1]
        logger.debug('equity1 in date in update_equity: {} {}'.format(equity, fill_event.date))
        logger.debug('realized_gain_and_loss in update_equity: {}'.format(self.realized_gain_and_loss.list))
        total_re_profit = sum(self.realized_gain_and_loss.list)
        # total_re_profit = self.realized_gain_and_loss.list[-1]
        logger.debug('total_re_profit in date in update_equity: {} {}'.format(total_re_profit, fill_event.date))
        logger.debug('self.realized_gain_and_loss.list: {}'.format(
            self.realized_gain_and_loss.list))
        logger.debug('self.realized_gain_and_loss.list: {}'.format(
            self.long_realized_gain_and_loss.list))
        logger.debug('self.realized_gain_and_loss.list: {}'.format(
            self.short_realized_gain_and_loss.list))
        total_profit = total_re_profit + self.unrealized_gain_and_loss.total()
        logger.debug('total_profit in date in update_equity: {} {}'.format(total_profit, fill_event.date))
        total_commission = sum(self.commission.list)
        last_commission = self.commission.list[-1]
        logger.debug('total_commission in date in update_equity: {} {}'.format(total_commission, fill_event.date))

        # buy_open = self.position[-2] == 0 and self.position[-1] > 0  # 买开仓，即做多
        # sell_open = self.position[-2] == 0 and self.position[-1] < 0  # 卖开仓，即做空
        # if buy_open or sell_open:
        #     equity = np.round(self.initial_cash + total_re_profit - last_commission, 2)
        # equity = np.round(self.initial_cash + total_profit - total_commission, 2)
        equity = np.round(self.initial_cash + total_re_profit - total_commission, 2)
        # if self.position[-1] != 0:  # 开仓后，权益计算需考虑滑点损耗
        #     equity -= 60 * fill_event.lots
        logger.debug('equity2 in date in update_equity: {} {}'.format(equity, fill_event.date))

        self.equity.add(fill_event.date, equity)

    def update_cash(self, fill_event):
        """
        更新现金，现金 = 资产余额 - 本次已缴纳的保证金
        """
        cur_equity = self.equity[-1]
        # total_margin = self.margin.total()
        margin = self.margin[-1]
        # cash = cur_equity - total_margin
        cash = np.round(cur_equity - margin, 2)
        logger.debug('fill_event.date, cash: {} {}'.format(fill_event.date, cash))
        logger.debug('cash in date: {} {}'.format(cash, fill_event.date))
        self.cash.add(fill_event.date, cash)

    def update_info(self, fill_event):
        """
        更新基本信息，更新信息后，删除重复的信息
        第一笔交易会删除update_time_index产生的初始化信息
        第二笔交易开始删除前一笔交易，慢慢迭代，最终剩下最后一笔交易获得的信息
        """
        # units = fill_event.units
        # lots = fill_event.lots
        # logger.info('units: {}'.format(units))
        # 更新顺序：仓位-均价-保证金、手续费-浮动盈亏-余额-可用资金
        self.update_position(fill_event)
        self.update_avg_price(fill_event)
        self.update_margin(fill_event)
        self.update_commission(fill_event)
        self.update_unrealized_gain_and_loss(fill_event)
        # self.update_equity(fill_event)
        # self.update_cash(fill_event)

        # self.position.del_last()
        # self.margin.del_last()
        # self.commission.del_last()
        # self.avg_price.del_last()
        # self.unrealized_gain_and_loss.del_last()
        # self.equity.del_last()
        # self.cash.del_last()

    def update_time_index(self, feed_list):
        """
        保持每日开盘后的数据更新，
        若当日无交易，则更新后的数据即为当日数据，
        若当日有交易，则交易后的数据覆盖开盘后更新的数据
        """
        date = feed_list[-1].cur_bar.cur_date
        logger.info('---------------------------------------------------------------')
        logger.info('update_time_index, 开盘后date in backtestfill: {}'.format(date))

        # for feed in feed_list:
        feed = feed_list[-1]
        # 控制计算的价格，同指令成交价一样
        price = feed.cur_bar.cur_close  # 取收盘价为计算价格
        # high = feed.cur_bar.cur_high
        # low = feed.cur_bar.cur_low
        logger.info('price in date in update_time_index: {} {}'.format(price, date))
        self.set_dataseries_instrument(feed.instrument)
        # self.position.copy_last(date)  # 更新仓位
        # logger.debug('self.position in backtestfill: {}'.format(self.position))
        # logger.info('self.position in backtestfill: {}'.format(self.position[-1]))
        logger.info('self.position[-1] in date in update_time_index: {} {}'.format(self.position[-1], date))

        # 更新保证金
        # margin = self.position[-1] * price * feed.per_margin * feed.mult
        # margin = feed.per_margin * feed.units * price * 300
        margin = self.margin[-1]  # 未持仓时，保证金 = 上一次开仓保证金 或 0（平仓后）
        logger.debug('feed.units: {}'.format(feed.units))
        # margin = abs(self.position[-1]) * price * feed.per_margin
        logger.debug('margin in date in update_time_index: {} {}'.format(margin, date))
        self.margin.add(date, margin)
        # 更新平均价格
        # self.avg_price.copy_last(date)
        # 更新手续费，注意期货手续费需要重新计算
        commission = 0  # 无交易进行时，手续费 = 0
        self.commission.add(date, commission)
        logger.debug('commission in date in update_time_index: {} {}'.format(self.commission[-1], date))
        # self.commission.add(date, commission)
        # 更新浮动盈亏
        cur_avg = self.avg_price[-1]
        self.avg_price.add(date, cur_avg)
        cur_position = self.position[-1]
        self.position.add(date, cur_position)
        logger.debug('cur_position, cur_avg in date update_time_index: {} {} {}'.format(cur_position, cur_avg, date))
        # 浮盈 = （卖出价 - 买入价）× 手数
        # 若卖出平仓，则原仓位为正，浮盈 = （平仓价（卖出）- 持仓均价）× 原仓位
        # 若买入平仓，则原仓位为负，浮盈 = （平仓价（买入）- 持仓均价）× 原仓位
        unrealized_g_l = np.round((price - cur_avg) * cur_position * feed.units, 2)
        if self.avg_price[-1] == 0:
            unrealized_g_l = 0
            # unrealized_g_l = unrealized_g_l_high = unrealized_g_l_low = 0
        logger.debug('cur_avg in date in update_time_index: {} {}'.format(cur_avg, date))
        logger.debug('unrealized_g_l in date in update_time_index: {} {}'.format(unrealized_g_l, date))
        self.unrealized_gain_and_loss.add(date, unrealized_g_l)

        # 更新equity
        last_equity = self.equity[-1]
        total_re_profit = sum(self.realized_gain_and_loss.list)
        logger.debug('total_re_profit: {}'.format(total_re_profit))
        logger.debug('self.realized_gain_and_loss.list: {}'.format(self.realized_gain_and_loss.list))
        total_profit = total_re_profit + self.unrealized_gain_and_loss.total()
        logger.debug('total_profit in date in update_time_index: {} {}'.format(total_profit, date))
        logger.debug('sum(self.commission.list) in date in update_time_index: {} {}'.format(
            sum(self.commission.list), date))
        # logger.debug('self.commission.list in date in update_time_index: {} {}'.format(self.commission.list, date))
        total_commission = np.round(sum(self.commission.list), 2)
        logger.debug('total_re_profit: {}'.format(total_re_profit))
        logger.debug('total_commission:{}'.format(total_commission))
        # 持仓时余额 = 上一次开仓后的余额 + 当日浮动盈亏
        equity = np.round(last_equity + unrealized_g_l, 2)
        logger.debug('equity in date in update_time_index: {} {}'.format(equity, date))
        self.equity.add(date, equity)

        # # 更新equity
        # commission = self.commission[-1]
        # total_re_profit = sum(self.realized_gain_and_loss.list)
        # total_profit = total_re_profit + self.unrealized_gain_and_loss.total()
        # logger.info('total_profit in date in update_time_index: {} {}'.format(total_profit, date))
        # total_profit_high = (
        #     total_re_profit + self.unrealized_gain_and_loss.total_high())
        # total_profit_low = (
        #     total_re_profit + self.unrealized_gain_and_loss.total_low())

        # equity = self.initial_cash + total_profit - commission
        # equity_high = self.initial_cash + total_profit_high - commission
        # equity_low = self.initial_cash + total_profit_low - commission
        # logger.info('equity in date in update_time_index: {} {}'.format(equity, date))
        # self.equity.add(date, equity, equity_high, equity_low)

        # 更新cash
        # total_margin = self.margin.total()
        logger.debug('total_margin in update_time_index: {}'.format(margin))
        if self.position[-1] == 0:
            cash = self.equity[-1]
        else:
            cash = np.round(self.equity[-1] - margin, 2)
        logger.debug('cash in date in update_time_index: {} {}'.format(cash, date))
        self.cash.add(date, cash)
        logger.info('####################################')

        # 检查是否爆仓
        if self.equity[-1] <= 0 or self.cash[-1] <= 0:
            for feed in feed_list:
                feed.continue_backtest = False
            logger.info('警告：策略已造成爆仓！')
            logger.info('####################################')

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
        logger.debug('last_position in backtestfill: {}'.format(last_position))
        # 情况四中不同种类的单
        extra_list = [
            'TAKE_PROFIT_ORDER', 'STOP_LOSS_ORDER', 'TRAILING_STOP_ORDER']

        date = fill_event.date
        lots = fill_event.lots
        logger.debug('lots in _update_trade_list: {}'.format(lots))
        logger.info('slippage in _update_trade_list: {}'.format(f.slippage))
        logger.info('slippage in _update_trade_list: {}'.format(type(f.slippage)))
        re_profit_list = self.realized_gain_and_loss.re_profit

        def get_re_profit(trade_lots, trade_code):
            """计算平仓盈亏和手续费"""
            if trade_code == 1:  # 做多
                buy_price = f.price  # + 0.2 * 1
                sell_price = i.price  # - 0.2 * 1
            elif trade_code == 0:  # 做空
                buy_price = i.price  # + 0.2 * 1
                sell_price = f.price  # - 0.2 * 1
            # re_profit = np.round((f.price - i.price) * trade_lots * f.units * i.direction, 2)
            re_profit = np.round((sell_price - buy_price) * trade_lots * f.units, 2)
            logger.info('re_profit: {} {} {} {} {} {}'.format(
                re_profit, f.price, i.price, trade_lots, f.units, i. direction))
            commission_ = np.round(f.units * f.price * f.per_comm * f.lots, 2)  # 平仓手续费
            # 单笔交易的手续费（即开仓手续费和平仓手续费之和）
            commission = commission_ + np.round(i.units * i.price * f.per_comm * i.lots, 2)
            re_profit_list.append(re_profit)
            # 加入累计的盈亏
            # self.realized_gain_and_loss.add(f.date, sum(re_profit_list))
            self.realized_gain_and_loss.add(f.date, re_profit)  # 记录每次盈亏
            logger.info('---self.realized_gain_and_loss.add---: {} {}'.format(
                self.realized_gain_and_loss.list, self.realized_gain_and_loss.dict))
            if i.direction > 0:  # 多头平仓盈亏（含手续费）
                self.realized_gain_and_loss.long_poisition_re_profit.append(re_profit - commission)
                self.long_realized_gain_and_loss.add(f.date, re_profit - commission)
                self.long_commission.add(f.date, commission)
            else:  # 空头平仓盈亏（含手续费）
                self.realized_gain_and_loss.short_position_re_profit.append(re_profit - commission)
                self.short_realized_gain_and_loss.add(f.date, re_profit - commission)
                self.short_commission.add(f.date, commission)
            logger.debug('self.realized_gain_and_loss in backtestfill: {}'.format(
                self.realized_gain_and_loss))
            logger.debug('self.realized_gain_and_loss.date in backtestfill: {}'.format(
                self.realized_gain_and_loss.date))
            if len(self.realized_gain_and_loss.date) > 1:
                if self.realized_gain_and_loss.date[-2] is f.date:
                    new_realized_g_l = (
                        self.realized_gain_and_loss[-1] + self.realized_gain_and_loss[-2])
                    # self.realized_gain_and_loss.update_cur(new_realized_g_l)
                    self.realized_gain_and_loss.add(date, new_realized_g_l)
                    self.realized_gain_and_loss.del_last()

        # 首先判断是否有情况四发生，即止盈、止损、移动止损
        if f.execute_type in extra_list:
            for i in self._trade_list:
                if f.order.parent is i:  # 找到父类，删除原空单，计算利润
                    self._trade_list.remove(i)
                    # self._completed_list.append((copy(i), copy(f)))
                    self._completed_list.append(copy(i))
                    self._completed_list.append(copy(f))
                    f.lots = 0

        else:
            # 判断情况一，即做多的情况
            if f.order_type == 'BUY' and last_position < 0:
                for i in self._trade_list:
                    # 剩余空单且品种相同
                    if f.instrument is i.instrument and i.order_type == 'SELL':
                        if f.lots == 0:
                            break
                        if i.lots > f.lots:  # 空单大于多单，剩余空单
                            index_i = self._trade_list.index(i)
                            self._trade_list.pop(index_i)  # 删除原空单
                            # self._completed_list.append((copy(i), copy(f)))
                            self._completed_list.append(copy(i))
                            self._completed_list.append(copy(f))
                            i.lots -= f.lots  # 修改抵消后剩余的空单
                            get_re_profit(f.lots, 1)  # 用执行交易的部分计算利润
                            f.lots = 0  # 没有多单了，单位设为0

                            if i.lots != 0:
                                # 修改后的单子放回原位
                                self._trade_list.insert(index_i, i)

                        elif i.lots <= f.lots:  # 空单小于多单，抵消后删除空单
                            self._trade_list.remove(i)
                            # self._completed_list.append((copy(i), copy(f)))
                            self._completed_list.append(copy(i))
                            self._completed_list.append(copy(f))
                            get_re_profit(i.lots, 1)  # 用执行交易的部分计算利润
                            f.lots -= i.lots  # 修改多单仓位，若为0，后面会删除

            # 判断情况二，即做空的情况
            elif f.order_type == 'SELL' and last_position > 0:
                for i in self._trade_list:
                    # 剩余多单且品种相同
                    if f.instrument is i.instrument and i.order_type == 'BUY':
                        if f.lots == 0:
                            break
                        if i.lots > f.lots:  # 多单大于空单，剩余多单
                            index_i = self._trade_list.index(i)
                            self._trade_list.pop(index_i)  # 删除原多单
                            # self._completed_list.append((copy(i), copy(f)))
                            self._completed_list.append(copy(i))
                            self._completed_list.append(copy(f))
                            i.lots -= f.lots  # 修改抵消后剩余的多单
                            get_re_profit(f.lots, 0)  # 用执行交易的部分计算利润
                            f.lots = 0  # 没有空单了，单位设为0

                            if i.lots != 0:
                                # 修改后的单子放回原位
                                self._trade_list.insert(index_i, i)

                        elif i.lots <= f.lots:  # 多单小于空单，抵消后删除多单
                            self._trade_list.remove(i)
                            # self._completed_list.append((copy(i), copy(f)))
                            self._completed_list.append(copy(i))
                            self._completed_list.append(copy(f))
                            get_re_profit(i.lots, 0)  # 用执行交易的部分计算利润
                            f.lots -= i.lots  # 修改空单仓位，若为0，后面会删除

    def __to_list(self, fill_event):
        """
        根据情况将order放入trade_list或order_list
        """
        if fill_event.execute_type in ['LIMIT', 'STOP']:
            self._order_list.append(fill_event)

        else:
            self._update_trade_list(fill_event)
            if fill_event.lots != 0:
                self._trade_list.append(fill_event)

    def run_fill(self, fill_event):
        """每次指令发过来后，先直接记录下来，然后再去对冲仓位"""
        self.set_dataseries_instrument(fill_event.instrument)
        self.update_info(fill_event)
        self.__to_list(fill_event)
        self.update_equity(fill_event)
        self.update_cash(fill_event)

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
            logger.debug('---------setting parent---------')

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
                        logger.debug('注意：止盈止损出现矛盾，已选择止损')
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
