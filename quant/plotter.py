# coding:utf-8
import pandas as pd
from quant.logging_backtest import logger
from plotly import graph_objs as go, offline as py


class PlotBase(object):
    """作图的基类，处理数据"""

    def __init__(self):
        pass


class Plotter(PlotBase):
    """作图展示"""

    def __init__(self, instrument, bar, fill):
        super().__init__()

        self.bar = bar.total_dict
        self.equity_df = fill.equity.df
        self.cash_df = fill.cash.df
        self.position_df = fill.position.df
        self.realized_G_L_df = fill.realized_gain_and_loss.df
        self.unrealized_g_l_df = fill.unrealized_gain_and_loss.df
        self.commission_df = fill.commission.df
        self.data = []
        self.update_menus = []

    def plot(self, instrument=None, engine='plotly', notebook=False):
        if engine == 'plotly':
            logger.debug('type(instrument): {}'.format(type(instrument)))
            if isinstance(instrument, str):
                df = pd.DataFrame(self.bar[instrument])
                df.set_index('time', inplace=True)
                df.index = pd.DatetimeIndex(df.index)
                p_symbol = go.Scatter(
                    x=df.index,
                    y=df.close,
                    xaxis='x3',
                    yaxis='y3',
                    name=instrument)
                self.data.append(p_symbol)

        # 调试用
        for position in self.position_df:
            p_position = go.Scatter(
                x=self.position_df.index,
                y=self.position_df[position],
                xaxis='x2',
                yaxis='y2',
                name='仓位')

        p_total = go.Scatter(
            x=self.equity_df.index,
            y=self.equity_df.equity,
            xaxis='x6',
            yaxis='y6',
            name='权益')

        p_cash = go.Scatter(
            x=self.cash_df.index,
            y=self.cash_df.cash,
            xaxis='x6',
            yaxis='y6',
            name='现金')

        p_realized_gain_and_loss = go.Scatter(
            x=self.realized_G_L_df.index,
            y=self.realized_G_L_df.realized_gain_and_loss,
            xaxis='x4',
            yaxis='y4',
            name='利润/亏损')

        p_unrealized_gain_and_loss = go.Scatter(
            x=self.unrealized_g_l_df.index,
            y=self.unrealized_g_l_df.unrealized_gain_and_loss,
            xaxis='x4',
            yaxis='y4',
            name='浮动盈亏')

        # # 调试用，全是0？？？
        # p_commission = go.Scatter(
        #     x=self.commission_df.index,
        #     y=self.commission_df.commission,
        #     xaxis='x4',
        #     yaxis='y4',
        #     name='手续费')

        self.data.append(p_position)
        self.data.append(p_total)
        self.data.append(p_cash)
        self.data.append(p_unrealized_gain_and_loss)
        self.data.append(p_realized_gain_and_loss)
        # self.data.append(p_commission)

        layout = go.Layout(
            xaxis2=dict(domain=[0, 1], anchor='y2', scaleanchor='x2', autorange=True),
            xaxis3=dict(domain=[0, 1], anchor='y3', scaleanchor='x2', autorange=True),
            xaxis4=dict(domain=[0, 1], anchor='y4', scaleanchor='x2', autorange=True),
            xaxis6=dict(domain=[0, 1], anchor='y6', scaleanchor='x2', autorange=True),
            yaxis2=dict(domain=[0, 0.15], scaleanchor='x2', autorange=True,),
            yaxis3=dict(domain=[0.15, 0.35], scaleanchor='x2', autorange=True,),
            yaxis4=dict(domain=[0.35, 0.85], scaleanchor='x2', autorange=True,),
            yaxis5=dict(
                domain=[0.15, 0.35],
                side='right',
                # range=[0, 10000000],
                autorange=True,
                overlaying='y3',
                tickvals=[0, 1000000, 2000000, 2500000],
                showgrid=False,
                scaleanchor='x2'),
            yaxis6=dict(domain=[0.85, 1], scaleanchor='x2', autorange=True))
        fig = go.Figure(data=self.data, layout=layout)
        if notebook:
            import plotly
            plotly.offline.init_notebook_mode()
            py.iplot(fig, filename='Strategy_Results.html', validate=False)
        else:
            py.plot(fig, filename='Strategy_Results.html', validate=False)
