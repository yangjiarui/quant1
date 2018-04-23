# coding:utf-8
import math
from datetime import datetime

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
import operator
from numpy.lib.stride_tricks import as_strided

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


def create_trade_log(completed_list, mult):
    """
    记录每比交易的明细，包括开仓日期、开仓价格、订单类型、手数、
    平仓日期、平仓价格、执行类型、收益、佣金及总收益等
    """
    trade_log_list = []
    for i in completed_list:
        f = i[1]

        d = {}
        d['entry_date'] = i[0].date
        d['entry_price'] = i[0].price
        d['order_type'] = i[0].order_type
        d['units'] = round(min(i[0].units, i[1].units), 3)
        d['exit_date'] = i[1].date
        d['exit_price'] = i[1].price
        d['pl_points'] = i[1].price - i[0].price
        d['execute_type'] = i[1].execute_type
        d['re_profit'] = (f.price - i[0].price) * d['units'] * mult * i[0].direction

        comm = f.per_comm * mult
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
    """"""
    if num_winning_trades(trade_log) == 0:
        return 0
    return np.average(_get_trade_bars(ts, trade_log, operator.gt))


def avg_bars_losing_trades(ts, trade_log):
    """"""
    if num_losing_trades(trade_log) == 0:
        return 0
    return np.average(_get_trade_bars(ts, trade_log, operator.lt))


# -------------------------回撤---------------------------

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

    dd['start_date'] = close[close == dd['peak']].index[0].strftime("%Y-%m-%d %H:%M:%S")
    dd['end_date'] = idx.strftime("%Y-%m-%d %H:%M:%S")
    close = close[close.index > idx]

    rd_mask = close > dd['peak']
    if rd_mask.any():
        dd['recovery_date'] = \
            close[rd_mask].index[0].strftime("%Y-%m-%d %H:%M:%S")
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
        dd['recovery_date'] = \
            high[rd_mask].index[0].strftime("%Y-%m-%d %H:%M:%S")
    return dd


def _windowed_view(x, window_units):
    """
    """
    y = as_strided(x, shape=(x.size - window_units + 1, window_units),
                   strides=(x.strides[0], x.strides[0]))
    return y


def rolling_max_dd(ser, period, min_periods=1):
    """
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

