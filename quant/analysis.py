# coding:utf-8
import math
import operator
from collections import OrderedDict
from datetime import datetime

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from numpy.lib.stride_tricks import as_strided
from .logging_backtest import logger

TRADING_DAYS_PER_YEAR = 252
TRADING_DAYS_PER_MONTH = 20
TRADING_DAYS_PER_WEEK = 5


def create_sharpe_ratio(returns, period=252):
    """
    计算夏普比率
    returns: Pandas Series，代表周期的百分比回报
    period：周期，日线（252），小时线（252*6.5），分钟线（252*6.5*60）
    """
    ratio = np.sqrt(period) * (np.mean(returns)) / np.std(returns)
    return ratio[0]


def create_drawdowns(equity_curve):
    """
    计算最大回撤
    计算高水位线（high-water mark)与权益线上的点的差值，其最大值即为最大回撤
    equity_curve：权益曲线，pandas series
    Return：最大回撤和持续时间，float
    """
    equity_curve.reset_index(drop=True, inplace=True)
    hwm = [0]
    eq_idx = equity_curve.index
    drawdown = pd.Series(index=eq_idx)
    duration = pd.Series(index=eq_idx)

    for t in range(1, len(eq_idx)):
        cur_hwm = max(hwm[t - 1], equity_curve[t])
        hwm.append(cur_hwm)
        drawdown[t] = hwm[t] - equity_curve[t]
        duration[t] = 0 if drawdown[t] == 0 else duration[t - 1] + 1
    return round(drawdown.max(), 5), round(duration.max(), 3)


def create_trade_log(completed_list, units):
    """
    记录每比交易的明细，包括开仓日期、开仓价格、订单类型、手数、
    平仓日期、平仓价格、执行类型、收益、佣金及总收益等
    """
    trade_log_list = []
    # logger.debug('completed_list: {}'.format(completed_list))
    logger.debug('len(completed_list): {}'.format(len(completed_list)))
    for i in completed_list:
        # logger.debug('i[0]: {}'.format(i[0]))
        # logger.debug('i[1]: {}'.format(i[1]))
        f = i[1]

        d = {}
        d['entry_date'] = i[0].date
        d['entry_price'] = i[0].price
        d['order_type'] = i[0].order_type
        logger.debug('i[0].date in analysis: {}'.format(i[0].date))
        logger.debug('i[0].price in analysis: {}'.format(i[0].price))
        logger.debug('i[0].order_type in analysis: {}'.format(i[0].order_type))
        logger.debug('i[0].units in analysis: {}'.format(i[0].units))
        logger.debug('i[1].units in analysis: {}'.format(i[1].units))
        d['units'] = round(min(i[0].units, i[1].units), 3)
        d['exit_date'] = i[1].date
        d['exit_price'] = i[1].price
        d['pl_points'] = i[1].price - i[0].price
        d['execute_type'] = i[1].execute_type
        d['re_profit'] = (
            (f.price - i[0].price) * d['units'] * units * i[0].direction)

        comm = f.per_comm * units
        d['commission'] = d['units'] * comm * f.price * 2
        trade_log_list.append(d)

    df = pd.DataFrame(trade_log_list)
    df['cumul_total'] = (df['re_profit'] - df['commission']).cumsum()
    return df[['entry_date', 'entry_price', 'order_type', 'units', 'exit_date',
               'exit_price', 'execute_type', 'pl_points', 're_profit',
               'commission', 'cumul_total']]


def _difference_in_years(start, end):
    """计算start和end两个日期间的年份差，365.2425为公历年"""
    diff = end - start
    diff_in_years = (diff.days + diff.seconds / 86400) / 365.2425
    return diff_in_years


def _get_trade_bars(ts, trade_log, op):
    """获取交易日期内的bar数据长度"""
    ll = []
    for i in range(len(trade_log.index)):
        if op(trade_log['re_profit'][i], 0):
            entry_date = trade_log['entry_date'][i]
            exit_date = trade_log['exit_date'][i]
            ll.append(len(ts[entry_date:exit_date].index))
    return ll


# -------------------------总体数据---------------------------

def beginning_balance(capital):
    """初始资金"""
    return capital


def ending_balance(dbal):
    """最终权益"""
    return dbal.iloc[-1]['balance']


def total_net_profit(trade_log):
    """净利润"""
    return trade_log.iloc[-1]['cumul_total']


def gross_profit(trade_log):
    """总盈利"""
    return trade_log[trade_log['re_profit'] > 0].sum()['re_profit']


def gross_loss(trade_log):
    """总亏损"""
    return trade_log[trade_log['re_profit'] < 0].sum()['re_profit']


def profit_factor(trade_log):
    """总盈利 / 总亏损"""
    if gross_profit(trade_log) == 0:
        return 0
    if gross_loss(trade_log) == 0:
        return 1000
    return gross_profit(trade_log) / gross_loss(trade_log) * (-1)


def return_on_initial_capital(trade_log, capital):
    """净利润 / 初始资金，即盈利率"""
    return total_net_profit(trade_log) / capital * 100


def annual_return_rate(end_balance, capital, start, end):
    """计算年复合增长率（compound annual growth rate）"""
    B = end_balance
    A = capital
    n = _difference_in_years(start, end)
    cagr = (math.pow(B / A, 1 / n) - 1) * 100
    return cagr


def trading_period(start, end):
    """交易周期"""
    diff = relativedelta(end, start)  # 计算日期差
    return '{} years {} months {} days'.format(diff.years, diff.months,
                                               diff.days)


def _true_func(arg1, arg2):
    return True


def _total_days_in_market(ts, trade_log):
    ll = _get_trade_bars(ts, trade_log, _true_func)
    return sum(ll)


def pct_time_in_market(ts, trade_log, start, end):
    return _total_days_in_market(ts, trade_log) / len(ts[start:end].index) * 100


# -------------------------次数统计---------------------------

def total_num_trades(trade_log):
    """交易笔数"""
    return len(trade_log.index)


def num_winning_trades(trade_log):
    """盈利次数"""
    return (trade_log['re_profit'] > 0).sum()


def num_losing_trades(trade_log):
    """亏损次数"""
    return (trade_log['re_profit'] < 0).sum()


def num_even_trades(trade_log):
    """持平次数"""
    return (trade_log['re_profit'] == 0).sum()


def pct_profitable_trades(trade_log):
    """盈利比率"""
    if total_num_trades(trade_log) == 0:
        return 0
    return num_winning_trades(trade_log) / total_num_trades(trade_log) * 100


# -------------------------盈利与亏损---------------------------

def avg_profit_per_trade(trade_log):
    """每比交易平均盈利"""
    if total_num_trades(trade_log) == 0:
        return 0
    return total_net_profit(trade_log) / total_num_trades(trade_log)


def avg_profit_per_winning_trade(trade_log):
    """每比盈利交易的平均盈利"""
    if num_winning_trades(trade_log) == 0:
        return 0
    return gross_profit(trade_log) / num_winning_trades(trade_log)


def avg_loss_per_losing_trade(trade_log):
    """每比交易平均亏损"""
    if num_losing_trades(trade_log) == 0:
        return 0
    return gross_loss(trade_log) / num_losing_trades(trade_log)


def ratio_avg_profit_win_loss(trade_log):
    """每比亏损交易的平均亏损"""
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

def num_winning_points(trade_log):
    """盈利点数"""
    if num_winning_trades(trade_log) == 0:
        return 0
    return trade_log[trade_log['pl_points'] > 0].sum()['pl_points']


def num_losing_points(trade_log):
    """亏损点数"""
    if num_losing_trades(trade_log) == 0:
        return 0
    return trade_log[trade_log['pl_points'] < 0].sum()['pl_points']


def total_net_points(trade_log):
    """盈亏点数"""
    return num_winning_points(trade_log) + num_losing_points(trade_log)


def avg_points(trade_log):
    """平均盈亏点数"""
    if total_num_trades(trade_log) == 0:
        return 0
    return trade_log['pl_points'].sum() / len(trade_log.index)


def largest_points_winning_trade(trade_log):
    """最大盈利点数"""
    if num_winning_trades(trade_log) == 0:
        return 0
    return trade_log[trade_log['pl_points'] > 0].max()['pl_points']


def largest_points_losing_trade(trade_log):
    """最大亏损点数"""
    if num_losing_trades(trade_log) == 0:
        return 0
    return trade_log[trade_log['pl_points'] < 0].min()['pl_points']


def avg_pct_gain_per_trade(trade_log):
    """"""
    if total_num_trades(trade_log) == 0:
        return 0
    df = trade_log['pl_points'] / trade_log['entry_price']
    return np.average(df) * 100


def largest_pct_winning_trade(trade_log):
    """"""
    if num_winning_trades(trade_log) == 0:
        return 0
    df = trade_log[trade_log['pl_points'] > 0]
    df = df['pl_points'] / df['entry_price']
    return df.max() * 100


def largest_pct_losing_trade(trade_log):
    """"""
    if num_losing_trades(trade_log) == 0:
        return 0
    df = trade_log[trade_log['pl_points'] < 0]
    df = df['pl_points'] / df['entry_price']
    return df.min() * 100


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


def avg_bars_winning_trades(ts, trade_log):
    """盈利交易中的平均 K 线数"""
    if num_winning_trades(trade_log) == 0:
        return 0
    return np.average(_get_trade_bars(ts, trade_log, operator.gt))


def avg_bars_losing_trades(ts, trade_log):
    """亏损交易中的平均 K 线数"""
    if num_losing_trades(trade_log) == 0:
        return 0
    return np.average(_get_trade_bars(ts, trade_log, operator.lt))


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


# -------------------------产生各种统计数据的主要调用函数---------------------------

def stats(ts, trade_log, dbal, start, end, capital):
    """
    计算交易后的统计数据
    Parameters：
        ts : Dataframe
            期货价格的 Time series (date, high, low, close, volume)
        trade_log : Dataframe
            交易日志 (entry_date, entry_price, long_short, qty,
            exit_date, exit_price, pl_points, re_profit, cumul_total)
        dbal : Dataframe
            每日的余额 (date, high, low, close)
        start : datetime
            第一次买入的日期
        end : datetime
            最后一次卖出的日期
        capital : float
            初始资金
    Returns：
        stats : 各个统计量的 Series
    """

    stats = OrderedDict()

    # 总体数据
    stats['start'] = start.strftime("%Y-%m-%d %H:%M:%S")
    stats['end'] = end.strftime("%Y-%m-%d %H:%M:%S")
    stats['beginning_balance'] = beginning_balance(capital)
    stats['ending_balance'] = ending_balance(dbal)
    stats['unrealized_profit'] = (
        ending_balance(dbal) - total_net_profit(trade_log) - (
            beginning_balance(capital)))
    stats['total_net_profit'] = total_net_profit(trade_log)
    stats['gross_profit'] = gross_profit(trade_log)
    stats['gross_loss'] = gross_loss(trade_log)
    stats['profit_factor'] = profit_factor(trade_log)
    stats['return_on_initial_capital'] = (
        return_on_initial_capital(trade_log, capital))
    cagr = annual_return_rate(dbal['balance'][-1], capital, start, end)
    stats['annual_return_rate'] = cagr
    stats['trading_period'] = trading_period(start, end)
    stats['pct_time_in_market'] = (
        pct_time_in_market(ts, trade_log, start, end))

    # 次数统计
    stats['total_num_trades'] = total_num_trades(trade_log)
    stats['num_winning_trades'] = num_winning_trades(trade_log)
    stats['num_losing_trades'] = num_losing_trades(trade_log)
    stats['num_even_trades'] = num_even_trades(trade_log)
    stats['pct_profitable_trades'] = pct_profitable_trades(trade_log)

    # 盈利与亏损
    stats['avg_profit_per_trade'] = avg_profit_per_trade(trade_log)
    stats['avg_profit_per_winning_trade'] = (
        avg_profit_per_winning_trade(trade_log))
    stats['avg_loss_per_losing_trade'] = avg_loss_per_losing_trade(trade_log)
    stats['ratio_avg_profit_win_loss'] = ratio_avg_profit_win_loss(trade_log)
    stats['largest_profit_winning_trade'] = (
        largest_profit_winning_trade(trade_log))
    stats['largest_loss_losing_trade'] = largest_loss_losing_trade(trade_log)

    # 点数
    stats['num_winning_points'] = num_winning_points(trade_log)
    stats['num_losing_points'] = num_losing_points(trade_log)
    stats['total_net_points'] = total_net_points(trade_log)
    stats['avg_points'] = avg_points(trade_log)
    stats['largest_points_winning_trade'] = (
        largest_points_winning_trade(trade_log))
    stats['largest_points_losing_trade'] = (
        largest_points_losing_trade(trade_log))
    stats['avg_pct_gain_per_trade'] = avg_pct_gain_per_trade(trade_log)
    stats['largest_pct_winning_trade'] = largest_pct_winning_trade(trade_log)
    stats['largest_pct_losing_trade'] = largest_pct_losing_trade(trade_log)

    # 连续次数
    stats['max_consecutive_winning_trades'] = (
        max_consecutive_winning_trades(trade_log))
    stats['max_consecutive_losing_trades'] = (
        max_consecutive_losing_trades(trade_log))
    stats['avg_bars_winning_trades'] = (
        avg_bars_winning_trades(ts, trade_log))
    stats['avg_bars_losing_trades'] = avg_bars_losing_trades(ts, trade_log)

    # 回撤
    dd = max_closed_out_drawdown(dbal['balance'])
    stats['max_closed_out_drawdown'] = dd['max']
    stats['max_closed_out_drawdown_start_date'] = dd['start_date']
    stats['max_closed_out_drawdown_end_date'] = dd['end_date']
    stats['max_closed_out_drawdown_recovery_date'] = dd['recovery_date']
    stats['drawdown_recovery'] = _difference_in_years(
        datetime.strptime(dd['start_date'], "%Y-%m-%d %H:%M:%S"),
        datetime.strptime(dd['end_date'], "%Y-%m-%d %H:%M:%S")) * -1
    stats['drawdown_annualized_return'] = dd['max'] / cagr
    # dd = max_intra_day_drawdown(dbal['balance_high'], dbal['balance_low'])
    # stats['max_intra_day_drawdown'] = dd['max']
    dd = rolling_max_dd(dbal['balance'], TRADING_DAYS_PER_YEAR)
    stats['avg_yearly_closed_out_drawdown'] = np.average(dd)
    stats['max_yearly_closed_out_drawdown'] = min(dd)
    dd = rolling_max_dd(dbal['balance'], TRADING_DAYS_PER_MONTH)
    stats['avg_monthly_closed_out_drawdown'] = np.average(dd)
    stats['max_monthly_closed_out_drawdown'] = min(dd)
    dd = rolling_max_dd(dbal['balance'], TRADING_DAYS_PER_WEEK)
    stats['avg_weekly_closed_out_drawdown'] = np.average(dd)
    stats['max_weekly_closed_out_drawdown'] = min(dd)

    # 回升
    ru = rolling_max_ru(dbal['balance'], TRADING_DAYS_PER_YEAR)
    stats['avg_yearly_closed_out_runup'] = np.average(ru)
    stats['max_yearly_closed_out_runup'] = ru.max()
    ru = rolling_max_ru(dbal['balance'], TRADING_DAYS_PER_MONTH)
    stats['avg_monthly_closed_out_runup'] = np.average(ru)
    stats['max_monthly_closed_out_runup'] = max(ru)
    ru = rolling_max_ru(dbal['balance'], TRADING_DAYS_PER_WEEK)
    stats['avg_weekly_closed_out_runup'] = np.average(ru)
    stats['max_weekly_closed_out_runup'] = max(ru)

    # 百分比变化
    pc = pct_change(dbal['balance'], TRADING_DAYS_PER_YEAR)
    stats['pct_profitable_years'] = (pc > 0).sum() / len(pc) * 100
    stats['best_year'] = pc.max()
    stats['worst_year'] = pc.min()
    stats['avg_year'] = np.average(pc)
    stats['annual_std'] = pc.std()
    pc = pct_change(dbal['balance'], TRADING_DAYS_PER_MONTH)
    stats['pct_profitable_months'] = (pc > 0).sum() / len(pc) * 100
    stats['best_month'] = pc.max()
    stats['worst_month'] = pc.min()
    stats['avg_month'] = np.average(pc)
    stats['monthly_std'] = pc.std()
    pc = pct_change(dbal['balance'], TRADING_DAYS_PER_WEEK)
    stats['pct_profitable_weeks'] = (pc > 0).sum() / len(pc) * 100
    stats['best_week'] = pc.max()
    stats['worst_week'] = pc.min()
    stats['avg_week'] = np.average(pc)
    stats['weekly_std'] = pc.std()

    # 比率
    stats['sharpe_ratio'] = sharpe_ratio(dbal['balance'].pct_change())
    stats['sortino_ratio'] = sortino_ratio(dbal['balance'].pct_change())

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
