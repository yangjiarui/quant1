# coding:utf-8
import math
import operator
from collections import OrderedDict
from datetime import datetime
from copy import copy
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from numpy.lib.stride_tricks import as_strided
from .logging_backtest import logger

TRADING_DAYS_PER_YEAR = 252
TRADING_DAYS_PER_MONTH = 20
TRADING_DAYS_PER_WEEK = 5
# np.set_printoptions(suppress=True)
# pd.set_option('precision', 4)
date = datetime.now().strftime('%Y-%m-%d-%H-%M')


def create_sharpe_ratio(returns, period=252):
    """
    计算夏普比率
    returns: Pandas Series，代表周期的百分比回报
    period：周期，日线（252），小时线（252*6.5），分钟线（252*6.5*60）
    """
    logger.info('-----returns-----: {}'.format(returns))
    ratio = np.sqrt(period) * (np.mean(returns)) / np.std(returns)
    logger.info('-----ratio-----: {} {}'.format(ratio, ratio[0]))
    return ratio[0]


def create_drawdowns(equity_curve: pd.DataFrame):
    """
    计算最大回撤、最大回撤比及对应的时间
    计算高水位线（high-water mark)与权益线上的点的差值，其最大值即为最大回撤
    Parameter: equity_curve, 权益曲线，pandas DataFrame(
                index=RangeIndex(start=0, stop=xxx, step=1), columns=['date', 'equity'])
    Return：drawdown, pd.DataFrame(columns=['date', 'equity', 'hwm', 'drawdown', 'pct'])
    """
    # logger.info('------------equity_curve-------------: {}'.format(equity_curve))
    # 去掉自动编号的index
    # equity_curve.reset_index(drop=True, inplace=True)
    eq_idx = equity_curve.index  # RangeIndex(start=0, stop=1199, step=1)
    logger.info('---------eq_idx---------: {}'.format(eq_idx))
    drawdown = pd.DataFrame(index=eq_idx, columns=['date', 'equity', 'drawdown', 'pct'])
    hwm = pd.Series(index=eq_idx, name='hwm')
    drawdown['date'] = equity_curve['date']
    drawdown['equity'] = equity_curve['equity']
    # 注意，要更改值，需先生成好数组再插入到 DataFrame 中，而不是直接更改 DataFrame 中的值
    hwm[0] = equity_curve['equity'][0]
    for t in range(1, len(eq_idx)):
        # 更改高水位线
        cur_hwm = max(drawdown['equity'][t], hwm[t - 1])
        hwm[t] = cur_hwm

    drawdown.insert(2, 'hwm', hwm)  # 插入高水位线
    drawdown['drawdown'] = (drawdown['hwm'] - drawdown['equity']).round(2)  # 计算回撤值，保留2位小数
    # logger.info('-------drawdown-----: {} {}'.format(type(drawdown), drawdown))
    # logger.info('-------drawdown-----: {}'.format(type(drawdown['drawdown']), drawdown['drawdown']))
    drawdown['pct'] = (drawdown['drawdown'] / drawdown['hwm']).round(4)  # 计算回撤比，保留4位小数
    # logger.info('-------drawdown-----: {} {}'.format(type(drawdown), drawdown))
    # with open('drawdown.txt', 'w') as f:
    #     f.write(str(copy(drawdown)))
    drawdown.to_csv(date + '_drawdown.csv', index=False)
    # logger.info('--------tpye of drawdown------: {}'.format(type(drawdown)))
    # logger.info('--------max_drawdown----------: {}'.format(drawdown['drawdown'].max()))
    return drawdown


def create_trade_log(completed_list, context):
    """
    记录每比交易的明细，包括开仓日期、开仓价格、订单类型、手数、
    平仓日期、平仓价格、执行类型、收益、佣金及总收益等
    """
    trade_log_list = []
    logger.debug('-----------completed_list----------: {}'.format(completed_list))
    logger.debug('len(completed_list): {}'.format(len(completed_list)))
    for i in completed_list:
        logger.debug('-----------i-------------: {}'.format(i))

        d = {}
        d['date'] = i.date
        d['price'] = i.price
        d['order_type'] = i.order_type
        d['lots'] = context.lots

        # position = context.fill.position.df
        # logger.info('----position----: {}'.format(position))
        # logger.info('----position----: {}'.format(position.index))
        position = context.fill.position.df[i.date:i.date].values[0][0]
        d['position'] = position
        logger.info('----position----: {} {}'.format(position, type(position)))
        logger.info('----position----: {}'.format(context.fill.position.df[i.date:i.date]))
        if position == 0:
            d['re_profit'] = context.fill.realized_gain_and_loss.df[i.date:i.date].values[0][0]
            logger.info('---d["re_profit"]---{}'.format(d['re_profit']))
        else:
            d['re_profit'] = 0
        comm = i.per_comm * i.units
        # d['commission'] = d['lots'] * comm * i.price
        d['commission'] = context.fill.commission.df[i.date:i.date].values[0][0]
        d['equity'] = context.fill.equity.df[i.date:i.date].values[0][0]
        logger.debug('----------d------------: {}'.format(d))
        trade_log_list.append(d)

    logger.debug('----realized_gain_and_loss analysis----: {} {}'.format(
        context.fill.realized_gain_and_loss.list, context.fill.realized_gain_and_loss.dict))
    logger.debug('---realized_gain_and_loss analysis---: {}'.format(
        context.fill.realized_gain_and_loss.df))
    df = pd.DataFrame(trade_log_list)
    # df['cumul_total'] = (df['re_profit'] - df['commission']).cumsum()
    # logger.info('---equity---: {}'.format(context.fill.equity.df[i.date:i.date]))
    # df['equity'] = context.fill.equity.df[i.date:i.date]['equity'].values[0]
    # logger.info('---equity---: {} {}'.format(df['equity'], type(df['equity'])))
    # return df[['entry_date', 'entry_price', 'order_type', 'lots', 'exit_date',
    #            'exit_price', 'execute_type', 'pl_points', 're_profit',
    #            'commission', 'cumul_total']]
    logger.debug('----------df------------: {}'.format(df))
    df = df[['date', 'price', 'order_type', 'lots', 'position', 'commission', 're_profit', 'equity']]
    logger.info('---df["re_profit"]---{} {}'.format(df[df['re_profit'] > 0], type(df['re_profit'])))
    return df


def _difference_in_years(start: pd.Timestamp, end: pd.Timestamp):
    """计算 start 和 end 两个日期间的年份差，以 365 为一年"""
    diff = end - start
    diff_in_years = (diff.days + diff.seconds / 86400) / 365
    return diff_in_years


def _difference_in_months(start: pd.Timestamp, end: pd.Timestamp):
    """计算 start 和 end 两个日期间的年份差，以 30 为一个月"""
    diff = end - start
    diff_in_months = (diff.days + diff.seconds / 86400) / 30
    return diff_in_months


def add_pct(number: int or float):
    return '{}%'.format(number)


def _get_trade_bars(
        ohlc_data: pd.DataFrame,
        trade_log: pd.DataFrame,
        op: operator) -> list:
    """
    获取交易日期内的 bar 数据长度列表，
    每一个值代表一次交易的持续周期，单位为 bar
    """
    lenth_bar = []
    open_date = None
    position = trade_log['position']
    position.index = trade_log['date']
    # logger.info('---position in _get_trade_bars---: {}'.format(position))
    # logger.info('---trade_log[re_profit]: {}'.format(trade_log['re_profit']))
    # logger.info('---trade_log[re_profit]: {}'.format(trade_log['re_profit'][0]))
    for i in range(len(trade_log.index)):
        if op(trade_log['re_profit'][i], 0):
            logger.info('--position.values[i]: {} {} {} {}'.format(
                i, position.values, position.values[i], type(int(position.values[i]))))
            position_ = int(position.values[i])
            if open_date is None and not position_:  # 无开仓时间且仓位为 0 ，不统计
                continue
            if int(position.values[i]):  # position != 0，表示开仓了
                if not open_date:  # 开仓后不重写开仓时间
                    logger.info('position.index: {} {}'.format(position.index, position))
                    open_date = position.index[i]  # 开仓时间
            else:  # position == 0，表示平仓了
                close_date = position.index[i]
                logger.info('--open_date, close_date--: {} {}'.format(open_date, close_date))
                lenth_bar.append(len(ohlc_data[open_date:close_date].index))
                open_date = None
    logger.info('---lenth_bar---: {}'.format(lenth_bar))
    return lenth_bar


# def _get_position_day(ohlc_data: pd.DataFrame, trade_log: pd.DataFrame) -> list:
#     day_list = []
#     open_date = None
#     position = trade_log['position']
#     for i in range(len(trade_log.index)):
#         if not open_date and not position.values[i]:
#             continue
#         if position.values[i]:
#             if not open_date:
#                 open_date = position.index[i].split()[0]
#             else:
#                 close_date = position.index[i]
#                 day_list.append(len(ohlc_data[open_date:close_date].index))


# -------------------------自定义数据---------------------------
def pct_profit_in_open(end_equity, capital, ohlc_data, trade_log):
    """持仓日年化收益率，当日只要交易了就算持仓"""
    position_list = _get_trade_bars(ohlc_data, trade_log, _true_func)
    position_day = sum(position_list) - len(position_list)  # 日线持仓情况
    logger.info('---position_day---: {} {} {}'.format(sum(position_list), len(position_list), position_day))
    profit = end_equity - capital
    rate = profit / (position_day / 365)
    return round(rate, 2)


# -------------------------总体数据---------------------------

def beginning_equity(capital):
    """初始资金"""
    return capital


def ending_equity(equity):
    """最终权益"""
    return round(equity.iloc[-1]['equity'], 2)


def total_net_profit(equity, capital):
    """净利润"""
    logger.info('--total_net_profit--:{} {}'.format(equity.iloc[-1], equity.iloc[-1]['equity']))
    return round(equity.iloc[-1]['equity'] - capital, 2)


def gross_profit(trade_log):
    """总盈利"""
    logger.info('---gross_profit---: {}'.format(trade_log[trade_log['re_profit'] > 0]['re_profit'].sum()))
    return round(trade_log[trade_log['re_profit'] > 0]['re_profit'].sum(), 2)


def gross_loss(trade_log):
    """总亏损，返回正值"""
    logger.info('---gross_loss---: {}'.format((-1) * trade_log[trade_log['re_profit'] < 0]['re_profit'].sum()))
    return round((-1) * trade_log[trade_log['re_profit'] < 0].sum()['re_profit'], 2)


def profit_factor(trade_log):
    """总盈利 / 总亏损，即盈亏比，总亏损为 0 时，返回 +0"""
    if gross_profit(trade_log) == 0:
        return 0
    if gross_loss(trade_log) == 0:  # 无亏损的情况
        return '+0'
    return round(gross_profit(trade_log) / gross_loss(trade_log), 2)


def return_rate(equity, capital):
    """净利润 / 初始资金，即盈利率"""
    return round(total_net_profit(equity, capital) / capital * 100, 2)


def annual_return_rate(equity, capital, start, end):
    """年化单利收益率（annual return rate）"""
    end_equity = equity['equity'][-1]
    profit = end_equity - capital
    n = _difference_in_years(start, end)
    rate = round((profit / capital) / n * 100, 2)
    return rate


def annual_compound_return_rate(equity, capital, start, end):
    """年化复利收益率（compound annual return rate）"""
    end_equity = equity['equity'][-1]
    n = _difference_in_years(start, end)
    rate = round((math.pow(end_equity / capital, 1 / n) - 1) * 100, 2)
    return rate


def monthly_return_rate(equity, capital, start, end):
    """月化单利收益率"""
    end_equity = equity['equity'][-1]
    n = _difference_in_months(start, end)
    rate = round(((end_equity - capital) / capital) / n * 100, 2)
    return rate


def monthly_compound_return_rate(equity, capital, start, end):
    """月化复利收益率"""
    end_equity = equity['equity'][-1]
    n = _difference_in_months(start, end)
    rate = round((math.pow(end_equity / capital, 1 / n) - 1) * 100, 2)
    return rate


def trading_period(start, end):
    """交易周期"""
    diff = relativedelta(end, start)  # 计算日期差
    return '{} years {} months {} days'.format(diff.years, diff.months, diff.days)


def initial_cash_rate(context, capital):
    """初始资金比例"""
    margin = context.fill.margin.df
    first_margin = margin[margin > 0][0]
    rate = np.round(first_margin / capital * 100, 2)


def _true_func(arg1, arg2):
    return True


def _total_days_in_market(ohlc_data, trade_log):
    ll = _get_trade_bars(ohlc_data, trade_log, _true_func)
    return sum(ll)


def pct_time_in_market(ohlc_data, trade_log, start, end):
    return _total_days_in_market(ohlc_data, trade_log) / len(ohlc_data[start:end].index) * 100


# -------------------------次数统计---------------------------

def num_total_trades(context):
    """交易次数，一次平仓算一次交易"""
    return len(context.fill.realized_gain_and_loss.list)


def num_winning_trades(context):
    """盈利次数"""
    df = context.fill.realized_gain_and_loss.df
    return len(df[df > 0])


def num_winning_long_trades(context):
    """多头盈利次数"""
    df = context.fill.long_realized_gain_and_loss.df
    return len(df[df > 0])


def num_winning_short_trades(context):
    """空头盈利次数"""
    df = context.fill.short_realized_gain_and_loss.df
    return len(df[df > 0])


def num_losing_trades(context):
    """亏损次数"""
    df = context.fill.realized_gain_and_loss.df
    return len(df[df < 0])


def num_losing_long_trades(context):
    """多头亏损次数"""
    df = context.fill.long_realized_gain_and_loss.df
    return len(df[df < 0])


def num_losing_short_trades(context):
    """空头亏损次数"""
    df = context.fill.short_realized_gain_and_loss.df
    return len(df[df < 0])


def num_even_trades(context):
    """持平次数"""
    df = context.fill.realized_gain_and_loss.df
    return len(df[df == 0])


def num_even_long_trades(context):
    """多头持平次数"""
    df = context.fill.long_realized_gain_and_loss.df
    return len(df[df == 0])


def num_even_short_trades(context):
    """空头持平次数"""
    df = context.fill.short_realized_gain_and_loss.df
    return len(df[df == 0])


def profitable_trades_rate(context):
    """盈利比率，盈利比率=盈利次数次数/总交易次数"""
    if num_total_trades(context) == 0:
        return 0
    return num_winning_trades(context) / num_total_trades(context)


def winning_rate(context):
    """胜率，胜率=非亏损次数/总交易次数"""
    if num_total_trades(context) == 0:
        return 0
    num = num_total_trades(context) - num_losing_trades(context)
    return num / num_total_trades(context)


# -------------------------盈利与亏损---------------------------

def avg_profit_per_trade(context):
    """每笔交易平均盈利"""
    equity = context.fill.equity.df
    capital = context.initial_cash
    if num_total_trades(context) == 0:
        return 0
    return total_net_profit(equity, capital) / num_total_trades(context)


def avg_profit_per_winning_trade(trade_log):
    """每笔盈利交易的平均盈利"""
    if num_winning_trades(trade_log) == 0:
        return 0
    return gross_profit(trade_log) / num_winning_trades(trade_log)


def avg_loss_per_losing_trade(trade_log):
    """每笔交易平均亏损"""
    if num_losing_trades(trade_log) == 0:
        return 0
    return gross_loss(trade_log) / num_losing_trades(trade_log)


def ratio_avg_profit_win_loss(trade_log):
    """每笔亏损交易的平均亏损"""
    if avg_profit_per_winning_trade(trade_log) == 0:
        return 0
    if avg_loss_per_losing_trade(trade_log) == 0:
        return 1000
    return (avg_profit_per_winning_trade(trade_log) /
            avg_loss_per_losing_trade(trade_log) * (-1))


def largest_profit_winning_trade(trade_log):
    """最大盈利"""
    if num_winning_trades(trade_log) == 0:
        return 0
    return trade_log[trade_log['re_profit'] > 0].max()['re_profit']


def largest_loss_losing_trade(trade_log):
    """最大亏损"""
    if num_losing_trades(trade_log) == 0:
        return 0
    return trade_log[trade_log['re_profit'] < 0].min()['re_profit']


# -------------------------点数---------------------------

# def num_winning_points(trade_log):
#     """盈利点数"""
#     if num_winning_trades(trade_log) == 0:
#         return 0
#     return trade_log[trade_log['pl_points'] > 0].sum()['pl_points']


# def num_losing_points(trade_log):
#     """亏损点数"""
#     if num_losing_trades(trade_log) == 0:
#         return 0
#     return trade_log[trade_log['pl_points'] < 0].sum()['pl_points']


# def total_net_points(trade_log):
#     """盈亏点数"""
#     return num_winning_points(trade_log) + num_losing_points(trade_log)


# def avg_points(trade_log):
#     """平均盈亏点数"""
#     if total_num_trades(trade_log) == 0:
#         return 0
#     return trade_log['pl_points'].sum() / len(trade_log.index)


# def largest_points_winning_trade(trade_log):
#     """最大盈利点数"""
#     if num_winning_trades(trade_log) == 0:
#         return 0
#     return trade_log[trade_log['pl_points'] > 0].max()['pl_points']


# def largest_points_losing_trade(trade_log):
#     """最大亏损点数"""
#     if num_losing_trades(trade_log) == 0:
#         return 0
#     return trade_log[trade_log['pl_points'] < 0].min()['pl_points']


# def avg_pct_gain_per_trade(trade_log):
#     """"""
#     if total_num_trades(trade_log) == 0:
#         return 0
#     df = trade_log['pl_points'] / trade_log['entry_price']
#     return np.average(df) * 100


# def largest_pct_winning_trade(trade_log):
#     """"""
#     if num_winning_trades(trade_log) == 0:
#         return 0
#     df = trade_log[trade_log['pl_points'] > 0]
#     df = df['pl_points'] / df['entry_price']
#     return df.max() * 100


# def largest_pct_losing_trade(trade_log):
#     """"""
#     if num_losing_trades(trade_log) == 0:
#         return 0
#     df = trade_log[trade_log['pl_points'] < 0]
#     df = df['pl_points'] / df['entry_price']
#     return df.min() * 100


# -------------------------连续次数---------------------------

def _subsequence(string, c):
    """
    判断字符串中连续的字符c的个数，如string：'001000001111100'，c：'0'，
    连续的字符c的个数为5
    """

    bit = 0
    count = 0
    maxlen = 0

    for i in range(len(string)):
        bit = string[i]

        if bit == c:
            count = count + 1
            if count > maxlen:
                maxlen = count
        else:
            count = 0
    return maxlen


def max_consecutive_winning_trades(trade_log):
    """最大持续盈利次数"""
    if num_winning_trades(trade_log) == 0:
        return 0
    return _subsequence(trade_log['re_profit'] > 0, True)


def max_consecutive_losing_trades(trade_log):
    """最大持续亏损次数"""
    if num_losing_trades(trade_log) == 0:
        return 0
    return _subsequence(trade_log['re_profit'] > 0, False)


def avg_bars_winning_trades(ohlc_data, trade_log):
    """盈利交易中的平均 K 线数"""
    if num_winning_trades(trade_log) == 0:
        return 0
    return np.average(_get_trade_bars(ohlc_data, trade_log, operator.gt))


def avg_bars_losing_trades(ohlc_data, trade_log):
    """亏损交易中的平均 K 线数"""
    if num_losing_trades(trade_log) == 0:
        return 0
    return np.average(_get_trade_bars(ohlc_data, trade_log, operator.lt))


# -------------------------回撤和回升---------------------------

def max_closed_out_drawdown(close):
    """"""
    running_max = close.expanding().max()
    cur_dd = (close - running_max) / running_max * 100
    dd_max = min(0, cur_dd.min())
    idx = cur_dd.idxmin()

    dd = pd.Series()
    dd['max'] = dd_max
    dd['peak'] = running_max[idx]
    dd['trough'] = close[idx]

    dd['start_date'] = (
        close[close == dd['peak']].index[0].strftime("%Y-%m-%d %H:%M:%S"))
    dd['end_date'] = idx.strftime("%Y-%m-%d %H:%M:%S")
    close = close[close.index > idx]

    rd_mask = close > dd['peak']
    if rd_mask.any():
        dd['recovery_date'] = close[rd_mask].index[0].strftime("%Y-%m-%d %H:%M:%S")
    else:
        dd['recovery_date'] = 'Not Recovered Yet'

    return dd


def max_intra_day_drawdown(high, low):
    """"""
    running_max = high.expanding().max()
    cur_dd = (low - running_max) / running_max * 100
    dd_max = min(0, cur_dd.min())
    idx = cur_dd.idxmin()

    dd = pd.Series()
    dd['max'] = dd_max
    dd['peak'] = running_max[idx]
    dd['trough'] = low[idx]
    dd['start_date'] = high[high == dd['peak']].index[0].strftime("%Y-%m-%d %H:%M:%S")
    dd['end_date'] = idx.strftime("%Y-%m-%d %H:%M:%S")
    high = high[high.index > idx]

    rd_mask = high > dd['peak']
    if rd_mask.any():
        dd['recovery_date'] = high[rd_mask].index[0].strftime("%Y-%m-%d %H:%M:%S")
    return dd


def _windowed_view(x, window_units):
    """
    为一个一维的数组创建一个二维的窗口视图（数组形式），
    x：一维数组
    例：
    >>> x = np.array([1, 2, 3, 4, 5, 6])
    >>> _windowed_view(x, 3)
    array([[1, 2, 3],
           [2, 3, 4],
           [3, 4, 5],
           [4, 5, 6]])
    """
    y = as_strided(x, shape=(x.size - window_units + 1, window_units),
                   strides=(x.strides[0], x.strides[0]))
    return y


def rolling_max_dd(ser, period, min_periods=1):
    """
    计算ser中滚动的最大回撤
    ser： Series
    min_periods： 1 <= min_periods <= window_units
    Return： 一维数组，长度为 len(x) - min_periods + 1
    """
    window_units = period + 1
    x = ser.values
    if min_periods < window_units:
        pad = np.empty(window_units - min_periods)
        pad.fill(x[0])
        x = np.concatenate((pad, x))
    y = _windowed_view(x, window_units)
    running_max_y = np.maximum.accumulate(y, axis=1)
    dd = (y - running_max_y) / running_max_y * 100
    rmdd = dd.min(axis=1)
    return pd.Series(data=rmdd, index=ser.index, name=ser.name)


def rolling_max_ru(ser, period, min_periods=1):
    """
    计算ser中的最大回升
    ser： Series
    min_periods： 1 <= min_periods <= window_units
    Return： 一维数组，长度为 len(x) - min_periods + 1
    """
    window_units = period + 1
    x = ser.values
    if min_periods < window_units:
        pad = np.empty(window_units - min_periods)
        pad.fill(x[0])
        x = np.concatenate((pad, x))
    y = _windowed_view(x, window_units)
    running_min_y = np.minimum.accumulate(y, axis=1)
    ru = (y - running_min_y) / running_min_y * 100
    rmru = ru.max(axis=1)
    return pd.Series(data=rmru, index=ser.index, name=ser.name)


# -------------------------百分比变化---------------------------

def pct_change(close, period):
    """数据上移period个位置，计算其变化的百分比"""
    diff = (close.shift(-period) - close) / close * 100
    diff.dropna(inplace=True)
    return diff


# -------------------------比率---------------------------

def sharpe_ratio(rets, risk_free=0.00, period=TRADING_DAYS_PER_YEAR):
    """
    根据每日的收益计算每日的夏普比率
    rets：一天的array或资金列表
    risk_free：无风险利率，默认为0%
    Return：每日的夏普比率
    """
    dev = np.std(rets, axis=0)
    mean = np.mean(rets, axis=0)
    sharpe = (mean * period - risk_free) / (dev * np.sqrt(period))
    return sharpe


def sortino_ratio(rets, risk_free=0.00, period=TRADING_DAYS_PER_YEAR):
    """
    根据每日的收益计算每日的索提诺比率，
    rets：一天的array或资金列表
    risk_free：无风险利率，默认为0%
    Return：每日的索提诺比率
    与夏普比率(Sharpe Ratio)有相似之处，但索提诺比率运用下偏标准差而不是总标准差，
    以区别不利和有利的波动。和夏普比率类似，这一比率越高，表明基金承担相同单位下行风
    险能获得更高的超额回报率。索提诺比率可以看做是夏普比率在衡量对冲基金/私募基金时
    的一种修正方式。
    """
    mean = np.mean(rets, axis=0)
    negative_rets = rets[rets < 0]
    dev = np.std(negative_rets, axis=0)
    sortino = (mean * period - risk_free) / (dev * np.sqrt(period))
    return sortino


# # -------------------------产生各种统计数据的主要调用函数---------------------------

# def stats(ts, trade_log, dbal, start, end, capital):
#     """
#     计算交易后的统计数据
#     Parameters：
#         ts : Dataframe
#             期货价格的 Time series (date, high, low, close, volume)
#         trade_log : Dataframe
#             交易日志 (entry_date, entry_price, long_short, qty,
#             exit_date, exit_price, pl_points, re_profit, cumul_total)
#         dbal : Dataframe
#             每日的余额 (date, high, low, close)
#         start : datetime
#             第一次买入的日期
#         end : datetime
#             最后一次卖出的日期
#         capital : float
#             初始资金
#     Returns：
#         stats : 各个统计量的 Series
#     """

#     stats = OrderedDict()

#     # 总体数据
#     stats['start'] = start.strftime("%Y-%m-%d %H:%M:%S")
#     stats['end'] = end.strftime("%Y-%m-%d %H:%M:%S")
#     stats['beginning_equity'] = beginning_equity(capital)
#     stats['ending_equity'] = ending_equity(dbal)
#     stats['unrealized_profit'] = (
#         ending_equity(dbal) - total_net_profit(trade_log) - (
#             beginning_equity(capital)))
#     stats['total_net_profit'] = total_net_profit(trade_log)
#     stats['gross_profit'] = gross_profit(trade_log)
#     stats['gross_loss'] = gross_loss(trade_log)
#     stats['profit_factor'] = profit_factor(trade_log)
#     stats['return_on_initial_capital'] = (
#         return_on_initial_capital(trade_log, capital))
#     cagr = annual_return_rate(dbal['equity'][-1], capital, start, end)
#     stats['annual_return_rate'] = cagr
#     stats['trading_period'] = trading_period(start, end)
#     stats['pct_time_in_market'] = (
#         pct_time_in_market(ts, trade_log, start, end))

#     # 次数统计
#     stats['total_num_trades'] = total_num_trades(trade_log)
#     stats['num_winning_trades'] = num_winning_trades(trade_log)
#     stats['num_losing_trades'] = num_losing_trades(trade_log)
#     stats['num_even_trades'] = num_even_trades(trade_log)
#     stats['pct_profitable_trades'] = pct_profitable_trades(trade_log)

#     # 盈利与亏损
#     stats['avg_profit_per_trade'] = avg_profit_per_trade(trade_log)
#     stats['avg_profit_per_winning_trade'] = (
#         avg_profit_per_winning_trade(trade_log))
#     stats['avg_loss_per_losing_trade'] = avg_loss_per_losing_trade(trade_log)
#     stats['ratio_avg_profit_win_loss'] = ratio_avg_profit_win_loss(trade_log)
#     stats['largest_profit_winning_trade'] = (
#         largest_profit_winning_trade(trade_log))
#     stats['largest_loss_losing_trade'] = largest_loss_losing_trade(trade_log)

#     # 点数
#     stats['num_winning_points'] = num_winning_points(trade_log)
#     stats['num_losing_points'] = num_losing_points(trade_log)
#     stats['total_net_points'] = total_net_points(trade_log)
#     stats['avg_points'] = avg_points(trade_log)
#     stats['largest_points_winning_trade'] = (
#         largest_points_winning_trade(trade_log))
#     stats['largest_points_losing_trade'] = (
#         largest_points_losing_trade(trade_log))
#     stats['avg_pct_gain_per_trade'] = avg_pct_gain_per_trade(trade_log)
#     stats['largest_pct_winning_trade'] = largest_pct_winning_trade(trade_log)
#     stats['largest_pct_losing_trade'] = largest_pct_losing_trade(trade_log)

#     # 连续次数
#     stats['max_consecutive_winning_trades'] = (
#         max_consecutive_winning_trades(trade_log))
#     stats['max_consecutive_losing_trades'] = (
#         max_consecutive_losing_trades(trade_log))
#     stats['avg_bars_winning_trades'] = (
#         avg_bars_winning_trades(ts, trade_log))
#     stats['avg_bars_losing_trades'] = avg_bars_losing_trades(ts, trade_log)

#     # 回撤
#     dd = max_closed_out_drawdown(dbal['equity'])
#     stats['max_closed_out_drawdown'] = dd['max']
#     stats['max_closed_out_drawdown_start_date'] = dd['start_date']
#     stats['max_closed_out_drawdown_end_date'] = dd['end_date']
#     stats['max_closed_out_drawdown_recovery_date'] = dd['recovery_date']
#     stats['drawdown_recovery'] = _difference_in_years(
#         datetime.strptime(dd['start_date'], "%Y-%m-%d %H:%M:%S"),
#         datetime.strptime(dd['end_date'], "%Y-%m-%d %H:%M:%S")) * -1
#     stats['drawdown_annualized_return'] = dd['max'] / cagr
#     # dd = max_intra_day_drawdown(dbal['equity_high'], dbal['equity_low'])
#     # stats['max_intra_day_drawdown'] = dd['max']
#     dd = rolling_max_dd(dbal['equity'], TRADING_DAYS_PER_YEAR)
#     stats['avg_yearly_closed_out_drawdown'] = np.average(dd)
#     stats['max_yearly_closed_out_drawdown'] = min(dd)
#     dd = rolling_max_dd(dbal['equity'], TRADING_DAYS_PER_MONTH)
#     stats['avg_monthly_closed_out_drawdown'] = np.average(dd)
#     stats['max_monthly_closed_out_drawdown'] = min(dd)
#     dd = rolling_max_dd(dbal['equity'], TRADING_DAYS_PER_WEEK)
#     stats['avg_weekly_closed_out_drawdown'] = np.average(dd)
#     stats['max_weekly_closed_out_drawdown'] = min(dd)

#     # 回升
#     ru = rolling_max_ru(dbal['equity'], TRADING_DAYS_PER_YEAR)
#     stats['avg_yearly_closed_out_runup'] = np.average(ru)
#     stats['max_yearly_closed_out_runup'] = ru.max()
#     ru = rolling_max_ru(dbal['equity'], TRADING_DAYS_PER_MONTH)
#     stats['avg_monthly_closed_out_runup'] = np.average(ru)
#     stats['max_monthly_closed_out_runup'] = max(ru)
#     ru = rolling_max_ru(dbal['equity'], TRADING_DAYS_PER_WEEK)
#     stats['avg_weekly_closed_out_runup'] = np.average(ru)
#     stats['max_weekly_closed_out_runup'] = max(ru)

#     # 百分比变化
#     pc = pct_change(dbal['equity'], TRADING_DAYS_PER_YEAR)
#     # RuntimeWarning:
#     # invalid value encountered in long_scalars
#     stats['pct_profitable_years'] = (pc > 0).sum() / len(pc) * 100
#     stats['best_year'] = pc.max()
#     stats['worst_year'] = pc.min()
#     stats['avg_year'] = np.average(pc)
#     stats['annual_std'] = pc.std()
#     pc = pct_change(dbal['equity'], TRADING_DAYS_PER_MONTH)
#     stats['pct_profitable_months'] = (pc > 0).sum() / len(pc) * 100
#     stats['best_month'] = pc.max()
#     stats['worst_month'] = pc.min()
#     stats['avg_month'] = np.average(pc)
#     stats['monthly_std'] = pc.std()
#     pc = pct_change(dbal['equity'], TRADING_DAYS_PER_WEEK)
#     stats['pct_profitable_weeks'] = (pc > 0).sum() / len(pc) * 100
#     stats['best_week'] = pc.max()
#     stats['worst_week'] = pc.min()
#     stats['avg_week'] = np.average(pc)
#     stats['weekly_std'] = pc.std()

#     # 比率
#     stats['sharpe_ratio'] = sharpe_ratio(dbal['equity'].pct_change())
#     stats['sortino_ratio'] = sortino_ratio(dbal['equity'].pct_change())

#     for i, j in stats.items():
#         if type(j) is not str:
#             stats[i] = round(j, 3)

#     return stats


# -------------------------产生各种统计数据的主要调用函数---------------------------

def stats(context):
    """
    计算交易后的统计数据
    Parameters：
        trade_log: Dataframe
            交易日志 ('date', 'price', 'order_type', 'lots',
                     'commission', 're_profit', 'equity')
        context: Context object, 全局变量
    Returns：
        stats : 各个统计量的 Series
    """
    ohlc_data = context.ohlc_data
    trade_log = context.trade_log
    logger.info('---trade_log.re_profit---{}'.format(trade_log['re_profit']))
    # trade_log = trade_log[trade_log['position'] == 0].reset_index(drop=True)  # 取平仓交易记录
    logger.info('---trade_log in analysis---: {}'.format(trade_log))
    equity = context.fill.equity.df
    start = equity.index[0]
    end = equity.index[-1]
    capital = context.initial_cash
    position = context.fill.position.df
    stats = OrderedDict()

    # 总体数据
    stats['测试天数'] = (end - start).days
    stats['测试周期数'] = context.count
    stats['测试开始时间'] = start.strftime("%Y-%m-%d %H:%M:%S")
    stats['测试结束时间'] = end.strftime("%Y-%m-%d %H:%M:%S")
    stats['指令总数'] = len(context.fill.completed_list)
    stats['初始资金'] = beginning_equity(capital)
    stats['最终权益'] = ending_equity(equity)
    stats['初始资金比例'] = 0
    # stats['unrealized_profit'] = (
    #     ending_equity(dbal) - total_net_profit(trade_log) - (
    #         beginning_equity(capital)))
    stats['净利润'] = total_net_profit(equity, capital)
    stats['总盈利'] = gross_profit(trade_log)
    stats['总亏损'] = gross_loss(trade_log)
    stats['盈亏比'] = profit_factor(trade_log)
    stats['盈利率'] = add_pct(
        return_rate(trade_log, capital))
    rate = annual_return_rate(equity, capital, start, end)
    stats['年化单利收益率'] = add_pct(rate)
    compound_rate = annual_compound_return_rate(equity, capital, start, end)
    stats['年化复利收益率'] = add_pct(compound_rate)
    # stats['测试周期数'] = context.test_days
    # stats['pct_time_in_market'] = (
    #     pct_time_in_market(ohlc_data, trade_log, start, end))
    stats['持仓日收益率'] = pct_profit_in_open(equity, capital, ohlc_data, trade_log)

    # 次数统计
    stats['交易次数'] = num_total_trades(context)
    stats['盈利次数'] = [num_winning_trades(context),
                        num_winning_long_trades(context),
                        num_winning_short_trades(context)]
    stats['亏损次数'] = [num_losing_trades(context),
                        num_losing_long_trades(context),
                        num_losing_short_trades(context)]
    stats['持平次数'] = num_even_trades(context)
    stats['盈利比率'] = profitable_trades_rate(context)
    stats['胜率'] = winning_rate(context)

    # 盈利与亏损
    stats['avg_profit_per_trade'] = avg_profit_per_trade(trade_log, capital)
    stats['avg_profit_per_winning_trade'] = (
        avg_profit_per_winning_trade(trade_log))
    stats['avg_loss_per_losing_trade'] = avg_loss_per_losing_trade(trade_log)
    stats['ratio_avg_profit_win_loss'] = ratio_avg_profit_win_loss(trade_log)
    stats['最大盈利'] = (
        largest_profit_winning_trade(trade_log))
    stats['最大亏损'] = largest_loss_losing_trade(trade_log)

    # 点数
    # stats['num_winning_points'] = num_winning_points(trade_log)
    # stats['num_losing_points'] = num_losing_points(trade_log)
    # stats['total_net_points'] = total_net_points(trade_log)
    # stats['avg_points'] = avg_points(trade_log)
    # stats['largest_points_winning_trade'] = (
    #     largest_points_winning_trade(trade_log))
    # stats['largest_points_losing_trade'] = (
    #     largest_points_losing_trade(trade_log))
    # stats['avg_pct_gain_per_trade'] = avg_pct_gain_per_trade(trade_log)
    # stats['largest_pct_winning_trade'] = largest_pct_winning_trade(trade_log)
    # stats['largest_pct_losing_trade'] = largest_pct_losing_trade(trade_log)

    # 连续次数
    stats['max_consecutive_winning_trades'] = (
        max_consecutive_winning_trades(trade_log))
    stats['max_consecutive_losing_trades'] = (
        max_consecutive_losing_trades(trade_log))
    stats['avg_bars_winning_trades'] = (
        avg_bars_winning_trades(ohlc_data, trade_log))
    stats['avg_bars_losing_trades'] = avg_bars_losing_trades(ohlc_data, trade_log)

    # 回撤
    dd = max_closed_out_drawdown(equity['equity'])
    logger.info('-----dd["start_date"]-------: {}'.format(dd['start_date']))  # 2013-07-03 00:00:00
    logger.info('-----type of dd["start_date"]-------: {}'.format(type(dd['start_date'])))  # str
    logger.debug('-----dd["start_date"].strptime-------: {}'.format(
        datetime.strptime(dd['start_date'], "%Y-%m-%d %H:%M:%S")))
    stats['max_closed_out_drawdown'] = dd['max']
    stats['max_closed_out_drawdown_start_date'] = dd['start_date']
    stats['max_closed_out_drawdown_end_date'] = dd['end_date']
    stats['max_closed_out_drawdown_recovery_date'] = dd['recovery_date']
    stats['drawdown_recovery'] = _difference_in_years(
        datetime.strptime(dd['start_date'], "%Y-%m-%d %H:%M:%S"),
        datetime.strptime(dd['end_date'], "%Y-%m-%d %H:%M:%S")) * -1
    cagr = annual_return_rate(equity['equity'][-1], capital, start, end)
    stats['drawdown_annualized_return'] = dd['max'] / cagr
    # dd = max_intra_day_drawdown(equity['equity_high'], equity['equity_low'])
    # stats['max_intra_day_drawdown'] = dd['max']
    dd = rolling_max_dd(equity['equity'], TRADING_DAYS_PER_YEAR)
    stats['avg_yearly_closed_out_drawdown'] = np.average(dd)
    stats['max_yearly_closed_out_drawdown'] = min(dd)
    dd = rolling_max_dd(equity['equity'], TRADING_DAYS_PER_MONTH)
    stats['avg_monthly_closed_out_drawdown'] = np.average(dd)
    stats['max_monthly_closed_out_drawdown'] = min(dd)
    dd = rolling_max_dd(equity['equity'], TRADING_DAYS_PER_WEEK)
    stats['avg_weekly_closed_out_drawdown'] = np.average(dd)
    stats['max_weekly_closed_out_drawdown'] = min(dd)

    # 回升
    ru = rolling_max_ru(equity['equity'], TRADING_DAYS_PER_YEAR)
    stats['avg_yearly_closed_out_runup'] = np.average(ru)
    stats['max_yearly_closed_out_runup'] = ru.max()
    ru = rolling_max_ru(equity['equity'], TRADING_DAYS_PER_MONTH)
    stats['avg_monthly_closed_out_runup'] = np.average(ru)
    stats['max_monthly_closed_out_runup'] = max(ru)
    ru = rolling_max_ru(equity['equity'], TRADING_DAYS_PER_WEEK)
    stats['avg_weekly_closed_out_runup'] = np.average(ru)
    stats['max_weekly_closed_out_runup'] = max(ru)

    # 百分比变化
    pc = pct_change(equity['equity'], TRADING_DAYS_PER_YEAR)
    # RuntimeWarning:
    # invalid value encountered in long_scalars
    stats['pct_profitable_years'] = (pc > 0).sum() / len(pc) * 100
    stats['best_year'] = pc.max()
    stats['worst_year'] = pc.min()
    stats['avg_year'] = np.average(pc)
    stats['annual_std'] = pc.std()
    pc = pct_change(equity['equity'], TRADING_DAYS_PER_MONTH)
    stats['pct_profitable_months'] = (pc > 0).sum() / len(pc) * 100
    stats['best_month'] = pc.max()
    stats['worst_month'] = pc.min()
    stats['avg_month'] = np.average(pc)
    stats['monthly_std'] = pc.std()
    pc = pct_change(equity['equity'], TRADING_DAYS_PER_WEEK)
    stats['pct_profitable_weeks'] = (pc > 0).sum() / len(pc) * 100
    stats['best_week'] = pc.max()
    stats['worst_week'] = pc.min()
    stats['avg_week'] = np.average(pc)
    stats['weekly_std'] = pc.std()

    # 比率
    stats['夏普比率'] = sharpe_ratio(equity['equity'].pct_change())
    stats['索提诺比率'] = sortino_ratio(equity['equity'].pct_change())

    for i, j in stats.items():
        if type(j) is not str:
            stats[i] = round(j, 3)

    return stats


# -------------------------下列函数调用前需先调用stats()---------------------------

def summary(stats, *metrics):
    """将stats的数据以DataDrame格式返回，必须先调用stats()函数"""
    index = []
    columns = ['strategy']
    data = []

    for metric in metrics:
        index.append(metric)
        data.append(stats[metric])

    df = pd.DataFrame(data, columns=columns, index=index)
    return df


def summary2(stats, benchmark_stats, *metrics):
    """将stats的数据和基准的stats数据以DataDrame格式返回，必须先调用stats()函数"""
    index = []
    columns = ['strategy', 'benchmark']
    data = []

    for metric in metrics:
        index.append(metric)
        data.append((stats[metric], benchmark_stats[metric]))

    df = pd.DataFrame(data, columns=columns, index=index)
    return df


def summary3(stats, benchmark_stats, *extras):
    """
    将stats的数据和基准的stats数据以DataDrame格式返回，必须先调用stats()函数
    同时，可添加额外参数计算stats的数据和基准的stats数据
    """
    index = ['annual_return_rate',
             'max_closed_out_drawdown',
             'drawdown_annualized_return',
             'pct_profitable_months',
             'best_month',
             'worst_month',
             'sharpe_ratio',
             'sortino_ratio']
    columns = ['strategy', 'benchmark']
    data = [(stats['annual_return_rate'],
             benchmark_stats['annual_return_rate']),
            (stats['max_closed_out_drawdown'],
             benchmark_stats['max_closed_out_drawdown']),
            (stats['drawdown_annualized_return'],
             benchmark_stats['drawdown_annualized_return']),
            (stats['pct_profitable_months'],
             benchmark_stats['pct_profitable_months']),
            (stats['best_month'],
             benchmark_stats['best_month']),
            (stats['worst_month'],
             benchmark_stats['worst_month']),
            (stats['sharpe_ratio'],
             benchmark_stats['sharpe_ratio']),
            (stats['sortino_ratio'],
             benchmark_stats['sortino_ratio'])]

    for extra in extras:
        index.append(extra)
        data.append((stats[extra], benchmark_stats[extra]))

    df = pd.DataFrame(data, columns=columns, index=index)
    return df
