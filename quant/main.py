# coding:utf-8
import queue
from collections import OrderedDict

import pandas as pd

from quant.analysis import (create_drawdowns, create_sharpe_ratio, create_trade_log,
                            stats)
from quant.backtestfill import BacktestFill
from quant.barbase import Bar
from quant.broker import Broker
from quant.dict_to_table import dict_to_table
from quant.event import events
from quant.logging_backtest import logger
from quant import plotter
from datetime import datetime
from quant.portfolio import Portfolio
# from quant.context import Context

date = datetime.now().strftime('%Y-%m-%d-%H-%M')
# context = Context()


class Quant(object):
    def __init__(self, context):
        self.feed_list = []
        self.strategy_list = []
        self.bar = None
        self.portfolio = None
        self.broker = None
        self.fill = None
        self.context = context

    def get_ready(self):
        """准备数据，设置参数"""
        feed_list = self.context.feed_list
        strategy_list = self.context.strategy
        portfolio = Portfolio
        self.set_backtest(feed_list, strategy_list, portfolio)
        commission = self.context.commission
        margin = self.context.margin
        units = self.context.units
        lots = self.context.lots
        slippage = self.context.slippage
        logger.debug('---slippage in main---:{}'.format(slippage))
        instrument = self.context.instrument
        self.set_commission(commission, margin, units, lots, slippage, instrument)
        self.set_cash(self.context.initial_cash)

    def run(self):
        """主循环"""
        self.__initialization()

        while True:
            try:
                event = events.get(False)  # 当 queue 为空时，raise queue.Empty
                logger.debug('events.qsize(): {}'.format(events.qsize()))
            except queue.Empty:
                self.__load_all_feed()  # 加载新行情
                logger.debug('self.__check_backtest_finished(): {}'.format(
                    self.__check_backtest_finished()))
                if not self.__check_backtest_finished():
                    # cur_bar中数据不足两条，不开始计算
                    if len(self.feed_list[-1].cur_bar._cur_bar_list) < 1:
                        # logger.debug('events.qsize(): {}'.format(events.qsize()))
                        continue
                    else:
                        self.__update_time_index()  # 更新基本信息
                        logger.debug('self.feed_list[-1].cur_bar.cur_date: {}'.format(
                            self.feed_list[-1].cur_bar.cur_date))
                        self.__check_pending_order()  # 检查订单是否成交

            else:
                if event.type == 'Market':
                    self.context.market_event.append(event)
                    self.__pass_to_market(event)  # 传递账户基本信息

                    for strategy in self.strategy_list:
                        strategy(event).run_strategy()

                elif event.type == 'Signal':
                    self.context.signal_event.append(event)
                    self.portfolio.run_portfolio(event)

                elif event.type == 'Order':
                    self.context.order_event.append(event)
                    self.broker.run_broker(event)

                elif event.type == 'Fill':
                    self.context.fill_event.append(event)
                    self.fill.run_fill(event)

                if self.__check_backtest_finished():
                    self.__output_summary()
                    break

    def __initialization(self):
        """对所有 feed 和 fill 内各项数据进行初始化"""
        logger.debug('feed_list in main initialization: {}'.format(self.feed_list))
        for feed in self.feed_list:
            feed.load_once()
            instrument = feed.instrument
            self.fill.position.initialize(instrument, 0)
            self.fill.margin.initialize(instrument, 0)
            self.fill.commission.initialize(instrument, 0)
            self.fill.long_commission.initialize(instrument, 0)
            self.fill.short_commission.initialize(instrument, 0)
            self.fill.avg_price.initialize(instrument, 0)
            self.fill.unrealized_gain_and_loss.initialize(instrument, 0)
            self.fill.realized_gain_and_loss.initialize(instrument, 0)
            self.fill.long_realized_gain_and_loss.initialize(instrument, 0)
            self.fill.short_realized_gain_and_loss.initialize(instrument, 0)
        self.fill.cash.initialize('all', self.fill.initial_cash)
        self.fill.equity.initialize('all', self.fill.initial_cash)

        self.__combine_all_feed()

    def __combine_all_feed(self):
        """只运行一次，创建一个空Bar，然后将所有feed都整合到一起"""
        self.bar = Bar('')
        self.bar._initialize()
        for feed in self.feed_list:
            logger.debug('feed.bar.total_dict in main: {}'.format(feed.bar.total_dict))
            self.bar._combine_all_feed(feed.bar.total_dict)

    def __load_all_feed(self):
        """加载新行情"""
        for feed in self.feed_list:
            feed.start()
            feed.prenext()
            feed.next()
            self.context.count += 1  # 计算 K 线数

    def __update_time_index(self):
        """每次更新行情后，根据新行情更新仓位、现金、保证金等账户基本信息"""
        self.fill.update_time_index(self.feed_list)
        logger.debug('len(self.feed_list) in main: {}'.format(len(self.feed_list)))
        logger.debug('self.feed_list in main: {}'.format(self.feed_list))
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

    def __add_data(self, feed_list):
        """添加行情到行情列表"""
        for data in feed_list:
            self.feed_list.append(data)

    def __add_strategy(self, strategy_list):
        """添加策略到列表"""
        for strategy in strategy_list:
            self.strategy_list.append(strategy)

    def __set_portfolio(self, portfolio):
        """添加处理信号模块"""
        self.portfolio = portfolio()

    def __set_broker(self, broker):
        """添加确认信号模块"""
        self.broker = broker()

    def __set_fill(self, fill):
        """添加交易记录模块"""
        self.fill = fill()
        self.context.fill = self.fill

    def set_execute_mode(self, execute_mode='open'):
        """
        execute_mode='open' 或 'close'，
        设置以当天收盘价close或第二天开盘价open为成交价
        """
        for feed in self.feed_list:
            feed.set_execute_mode(execute_mode)

    def set_trailing_stop_price(self, trailing_stop_price='open'):
        """
        execute_mode='open' 或 'close'，
        设置以当天收盘价close或第二天开盘价open为移动止损价
        """
        for feed in self.feed_list:
            feed.set_trailing_stop_execute_mode(trailing_stop_price)

    def set_buffer(self, buffer_days=10):
        """设置buffer天数，用于计算参数前提前加载参数"""
        for feed in self.feed_list:
            feed.set_buffer_days(buffer_days)

    def set_backtest(self, feed_list, strategy_list, portfolio):
        """设置回测"""
        if not isinstance(feed_list, list):
            feed_list = [feed_list]
        if not isinstance(strategy_list, list):
            strategy_list = [strategy_list]

        # 按回测流程顺序一次引用各模块
        self.__add_data(feed_list)
        self.__add_strategy(strategy_list)
        self.__set_portfolio(portfolio)
        self.__set_broker(Broker)
        self.__set_fill(BacktestFill)
        self.set_execute_mode('open')
        self.set_trailing_stop_price('open')
        self.set_buffer(10)

    def set_commission(self, commission, margin, units, lots, slippage, instrument=None):
        """
        设置手续费、保证金、合约单位及合约品种等参数
        commission：手续费，0.0003表示每手收取0.03%的手续费
        margin：保证金比例，通常为0.05-0.15
        units：合约单位，一般为吨/手
        lots:下单手数
        """
        for feed in self.feed_list:
            if feed.instrument == instrument or instrument is None:
                feed.set_per_comm(commission)
                feed.set_per_margin(margin)
                feed.set_units(units)
                feed.set_lots(lots)
                feed.set_slippage(slippage)
                logger.debug('---slippage in feed main---:{}'.format(feed.slippage))

    def set_cash(self, cash=500000):
        """设置初始资金"""
        self.fill.set_cash(cash)

    def set_notify(self):
        """设置交易提醒"""
        self.broker.set_notify()

    def __output_summary(self):
        """输出简略的回测结果"""
        total = pd.DataFrame(self.fill.equity.dict)
        logger.debug('-----------self.fill.equity-------------: {}'.format(self.fill.equity))
        logger.debug('-------total---------: {}'.format(total))
        # with open('total.txt', 'w') as f:
        #     # f.write(str(total))
        #     for index, row in total.iterrows():
        #         f.write(str(row['date']))
        #         f.write(str(','))
        #         f.write(str(row['equity']))
        #         f.write('\n')
        logger.debug('-----------total.index----------: {}'.format(total.index))
        logger.debug('-----------total.columns----------: {}'.format(total.columns))
        drawdown = create_drawdowns(total)
        logger.debug('----------------drawdown done----------')
        # 计算列中的后一个元素与前一个元素差的百分比
        total.set_index('date', inplace=True)  # 去掉 date，保留 equity
        pct_returns = total.pct_change()
        logger.debug('------------pct_change------------')
        total /= self.fill.initial_cash
        logger.debug('-----------total /--------------')
        # max_drawdown_pct, duration_for_pct = create_drawdowns(total['equity'])
        # logger.info('------------max_drawdown, duration----------: {} {}'.format(max_drawdown_pct, duration_for_pct))
        # logger.info('------------max_drawdown, duration----------: {} {}'.format(max_drawdown_value, duration_for_value))
        # 计算测试天数
        date_type = '%Y-%m-%d'
        start_date = datetime.strptime(self.context.start_date, date_type)
        end_date = datetime.strptime(self.context.end_date, date_type)
        self.context.test_days = (end_date - start_date).days
        results = OrderedDict()
        results['测试开始时间'] = self.context.start_date
        results['测试结束时间'] = self.context.end_date
        results['测试天数'] = self.context.test_days  # 从测试数据开始到结束的天数
        results['测试周期'] = self.context.count  # 测试数据的 K 线数
        results['指令总数'] = len(self.fill.completed_list)  # 指令总数
        results['初始资金'] = self.fill.initial_cash
        results['最终权益'] = round(self.fill.equity[-1], 2)  # 最终权益
        logger.info('------------results-----------: {}'.format(results))
        total_return = round(results['最终权益'] / self.fill.initial_cash - 1, 4)
        logger.info('------------total_return-----------: {}'.format(total_return))
        results['夏普比率'] = round(create_sharpe_ratio(pct_returns), 2)
        results['盈利率'] = str(round(total_return * 100, 2)) + '%'
        results['最大回撤'] = drawdown['drawdown'].max()
        results['最大回撤时间'] = drawdown['date'][drawdown['drawdown'].idxmax()]  # 只能找出一个 index
        results['最大回撤比'] = str(round(drawdown['pct'].max() * 100, 2)) + '%'
        results['最大回撤比时间'] = drawdown['date'][drawdown['pct'].idxmax()]
        logger.debug('----short_realized_gain_and_loss----: {}'.format(
            self.fill.short_realized_gain_and_loss.dict))
        logger.debug('---type of short_realized_gain_and_loss.list---: {}'.format(
            type(self.fill.short_realized_gain_and_loss.list)))
        logger.debug('---short_realized_gain_and_loss.list---: {}'.format(
            self.fill.short_realized_gain_and_loss.list))

        long_profit = [i for i in self.fill.long_realized_gain_and_loss.list if i >= 0]
        long_loss = [i for i in self.fill.long_realized_gain_and_loss.list if i < 0]
        long_commission = self.fill.long_commission.list
        short_profit = [i for i in self.fill.short_realized_gain_and_loss.list if i >= 0]
        short_loss = [i for i in self.fill.short_realized_gain_and_loss.list if i < 0]
        short_commission = self.fill.short_commission.list
        logger.debug('---self.fill.long_realized_gain_and_loss.list---: {}'.format(
            self.fill.long_realized_gain_and_loss.list))
        logger.debug('---self.fill.short_realized_gain_and_loss.list---: {}'.format(
            self.fill.short_realized_gain_and_loss.list))
        logger.debug('----long_profit, long_loss---: {} {}'.format(long_profit, long_loss))
        logger.debug('----long_commission---: {}'.format(long_commission))
        logger.debug('----short_profit, short_loss---: {} {}'.format(short_profit, short_loss))
        logger.debug('----short_commission---: {}'.format(short_commission))
        results['多头总盈利'] = round(sum(long_profit), 2)
        results['多头总亏损'] = round(sum(long_loss), 2)
        results['空头总盈利'] = round(sum(short_profit), 2)
        results['空头总亏损'] = round(sum(short_loss), 2)
        results['手续费'] = sum(long_commission) + sum(short_commission)
        logger.info('---------results---------: {}'.format(results))
        results_table = dict_to_table(results)
        with open(date + '_results.txt', 'w') as f:
            f.write(results_table)

    def get_trade_log(self, instrument):
        """获取交易记录"""
        completed_list = self.fill.completed_list
        for feed in self.feed_list:
            if feed.instrument is instrument:
                return create_trade_log(completed_list, self.context)

    def get_analysis(self, instrument):
        """输出详细的结果分析"""
        logger.info('-----get_analysis-----')
        ohlc_data = self.feed_list[0].bar.df
        ohlc_data = ohlc_data.drop(len(ohlc_data) - 1)  # 最后一条数据为重复的数据
        logger.debug('---feed_list---: {} {}'.format(self.feed_list, self.feed_list[0].bar))
        ohlc_data.set_index('time', inplace=True)  # 设立新索引
        ohlc_data.index = pd.DatetimeIndex(ohlc_data.index)  # 将新索引转换为 DatetimeIndex
        logger.debug('------ohlc_data.index------: {}'.format(ohlc_data.index))
        logger.debug('------type of ohlc_data.index------: {}'.format(type(ohlc_data.index)))
        self.context.ohlc_data = ohlc_data  # pd.DataFrame

        dbal = self.fill.equity.df  # 权益
        start = dbal.index[0]  # 开始日期
        end = dbal.index[-1]  # 结束日期
        logger.debug('----start----: {}'.format(start))
        logger.debug('----end----: {}'.format(end))
        logger.debug('----type of end----: {}'.format(type(end)))
        logger.debug('----context.start_date----: {}'.format(self.context.start_date))
        logger.debug('----context.end_date----: {}'.format(self.context.end_date))
        logger.debug('----type of context.end_date----: {}'.format(type(self.context.end_date)))
        # capital = self.fill.initial_cash  # 初始资金
        trade_log = self.get_trade_log(instrument)
        # logger.info('------trade_log-----: {}'.format(trade_log))
        trade_log = trade_log[trade_log['lots'] != 0]
        trade_log.to_csv(date + '_trade_log.csv')
        self.context.trade_log = trade_log
        logger.info('------trade_log-----: {}'.format(trade_log))
        logger.debug('------context.fill-----: {}'.format(
            self.context.fill.long_realized_gain_and_loss.df))
        trade_log.reset_index(drop=True, inplace=True)
        analysis = stats(self.context)
        logger.info('----------------------stats-----------------------')
        logger.debug('---analysis_table---: {}'.format(analysis))
        equity = self.context.fill.equity.df
        equity.to_csv(date + '_equity.csv')
        analysis_table = dict_to_table(analysis)
        with open(date + '_analysis_table.txt', 'w') as f:
            f.write(str(analysis_table))
        logger.info('analysis_table: {}'.format(analysis_table))

    def plot(self, instrument, engine='plotly', notebook=False):
        """画图展示"""
        data = plotter.Plotter(
            instrument=instrument,
            bar=self.bar,
            fill=self.fill
        )
        data.plot(instrument=instrument, engine=engine, notebook=notebook)

    def plot_partly(self, instrument, engine='plotly', notebook=False):
        """画图展示"""
        data = plotter.Plotter(
            instrument=instrument,
            bar=self.bar,
            fill=self.fill
        )
        data.plot_partly(instrument=instrument, engine=engine, notebook=notebook)
