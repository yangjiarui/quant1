# coding:utf-8
import pandas as pd
from quant.logging_backtest import logger
from plotly import graph_objs as go, offline as py
from datetime import datetime

date = datetime.now().strftime('%Y-%m-%d-%H-%M')


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
        self.data_dict = {
            '权益': self.equity_df,
            '现金': self.cash_df,
            '平仓盈亏': self.realized_G_L_df,
            '浮动盈亏': self.unrealized_g_l_df,
        }

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
                    xaxis='x2',
                    yaxis='y2',
                    name=instrument)
                self.data.append(p_symbol)

        # 调试用
        for position in self.position_df:
            p_position = go.Scatter(
                x=self.position_df.index,
                y=self.position_df[position],
                xaxis='x7',
                yaxis='y7',
                name='仓位')

        p_equity = go.Scatter(
            x=self.equity_df.index,
            y=self.equity_df.equity,
            xaxis='x3',
            yaxis='y3',
            name='权益')

        p_cash = go.Scatter(
            x=self.cash_df.index,
            y=self.cash_df.cash,
            xaxis='x4',
            yaxis='y4',
            name='现金')

        p_realized_gain_and_loss = go.Scatter(
            x=self.realized_G_L_df.index,
            y=self.realized_G_L_df.realized_gain_and_loss,
            xaxis='x5',
            yaxis='y5',
            name='利润/亏损')

        p_unrealized_gain_and_loss = go.Scatter(
            x=self.unrealized_g_l_df.index,
            y=self.unrealized_g_l_df.unrealized_gain_and_loss,
            xaxis='x6',
            yaxis='y6',
            name='浮动盈亏')

        # # 调试用，全是0？？？
        # p_commission = go.Scatter(
        #     x=self.commission_df.index,
        #     y=self.commission_df.commission,
        #     xaxis='x4',
        #     yaxis='y4',
        #     name='手续费')

        self.data.append(p_position)
        self.data.append(p_equity)
        self.data.append(p_cash)
        self.data.append(p_unrealized_gain_and_loss)
        self.data.append(p_realized_gain_and_loss)
        # self.data.append(p_commission)

        layout = go.Layout(
            xaxis2=dict(domain=[0, 1], anchor='y2', scaleanchor='x2', autorange=True),
            xaxis3=dict(domain=[0, 1], anchor='y3', scaleanchor='x2', autorange=True),
            xaxis4=dict(domain=[0, 1], anchor='y4', scaleanchor='x2', autorange=True),
            xaxis5=dict(domain=[0, 1], anchor='y5', scaleanchor='x2', autorange=True),
            xaxis6=dict(domain=[0, 1], anchor='y6', scaleanchor='x2', autorange=True),
            xaxis7=dict(domain=[0, 1], anchor='y7', scaleanchor='x2', autorange=True),
            yaxis2=dict(domain=[0, 0.2], scaleanchor='x2', autorange=True,),
            yaxis3=dict(domain=[0.2, 0.4], scaleanchor='x2', autorange=True,),
            yaxis4=dict(domain=[0.4, 0.6], scaleanchor='x2', autorange=True,),
            # yaxis5=dict(
            #     domain=[0.15, 0.35],
            #     side='right',
            #     # range=[0, 10000000],
            #     autorange=True,
            #     overlaying='y3',
            #     tickvals=[0, 1000000, 2000000, 2500000],
            #     showgrid=False,
            #     scaleanchor='x2'),
            yaxis5=dict(domain=[0.6, 0.8], scaleanchor='x2', autorange=True),
            yaxis6=dict(domain=[0.8, 0.9], scaleanchor='x2', autorange=True),
            yaxis7=dict(domain=[0.9, 1], scaleanchor='x2', autorange=True))
        fig = go.Figure(data=self.data, layout=layout)
        if notebook:
            import plotly
            plotly.offline.init_notebook_mode()
            py.iplot(fig, filename='Strategy_Results.html', validate=False)
        else:
            py.plot(fig, filename='Strategy_Results.html', validate=False)

    def plot_profit(self, instrument=None, engine='plotly', notebook=False):
        if engine == 'plotly':
            if isinstance(instrument, str):
                df = pd.DataFrame(self.bar[instrument])
                df.set_index('time', inplace=True)
                df.index = pd.DatetimeIndex(df.index)

        p_realized_gain_and_loss = go.Scatter(
            x=self.realized_G_L_df.index,
            y=self.realized_G_L_df.realized_gain_and_loss,
            xaxis='x5',
            yaxis='y5',
            name='利润/亏损')

        self.data.append(p_realized_gain_and_loss)
        layout = go.Layout(
            xaxis2=dict(domain=[0, 1], anchor='y2', scaleanchor='x2', autorange=True),
            yaxis2=dict(domain=[0, 0.2], scaleanchor='x2', autorange=True,))
        fig = go.Figure(data=self.data, layout=layout)
        if notebook:
            import plotly
            plotly.offline.init_notebook_mode()
            py.iplot(fig, filename='Realized_gain_and_loss.html', validate=False)
        else:
            py.plot(fig, filename='Realized_gain_and_loss.html', validate=False)

    def _plot_partly(self, name, value, instrument=None, engine='plotly', notebook=False):
        if engine == 'plotly':
            if isinstance(instrument, str):
                df = pd.DataFrame(self.bar[instrument])
                df.set_index('time', inplace=True)
                df.index = pd.DatetimeIndex(df.index)

        p_data = go.Scatter(
            x=value.index,
            y=value[value.columns[0]],
            xaxis='x2',
            yaxis='y2',
            name=name)

        self.data.append(p_data)
        layout = go.Layout(
            xaxis2=dict(domain=[0, 1], anchor='y2', scaleanchor='x2', autorange=True),
            yaxis2=dict(domain=[0, 1], scaleanchor='x2', autorange=True,))
        fig = go.Figure(data=self.data, layout=layout)
        return fig

    def plot_partly(self, instrument=None, engine='plotly', notebook=False):
        for name, value in self.data_dict.items():
            fig = self._plot_partly(name, value, instrument, engine, notebook)
        if notebook:
            import plotly
            plotly.offline.init_notebook_mode()
            py.iplot(fig, filename=date + '_策略收益情况.html', validate=False)
        else:
            py.plot(fig, filename=date + '_策略收益情况.html', validate=False)
