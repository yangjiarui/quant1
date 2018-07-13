AIQuant

---

[TOC]

## 简介
AIQuant 回测框架
## 快速上手
### 环境准备
要使用 AIQuant 回测框架，首先需要做一些简单的环境准备。

* 安装Python
在 https://www.python.org/downloads/ 获取最新版本的 Python。
安装后，打开 shell，输入 python，应该得到下列内容：
```
Python 3.6.4
[GCC 4.8.4] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>>
```
查看 pip 是否一同安装好了，重新打开一个 shell 或者在刚才的 shell 里输入 `exit()`，输入：
```
pip --version
# or
pip3 --version
```
得到：
```
pip 10.0.1 from /xxx/python3.6/site-packages/pip (python 3.6)
```

* （可选）安装虚拟环境
参考 http://pythonguidecn.readthedocs.io/zh/latest/dev/virtualenvs.html，任选一种方式即可。

### 安装及设置
* 安装
建议在虚拟环境中进行安装，这样不会打乱系统的包配置。
下载代码：
```
git clone https://z123zero@bitbucket.org/z123zero/quant.git
cd quant
pip install -r requirements.txt
```
* 设置
参考 http://python3-cookbook-personal.readthedocs.io/zh_CN/latest/c10/p09_add_directories_to_sys_path.html，将第三方库加入 Python 路径。
创建一个.pth文件，将目录列举出来，像这样：
```
# quant.pth
/somewhere/quant
```
把这个.pth文件需要放在Python的site-packages目录，通常位于/usr/local/lib/python3.x/site-packages 或者 ~/.local/lib/python3.x/sitepackages。当解释器启动时，.pth文件里列举出来的存在于文件系统的目录将被添加到sys.path。
### 使用
* 运行示例
```
cd tests/
python my_strategy.py
```
即可查看运行结果。

* 编辑自己的策略
可以在任意目录新建自己的策略文件（Python 文件），基础的导入模块如下：
```python
# your_strategy.py
from quant.strategy import Strategy
from quant.main import Quant
from quant.feedbase import CSV
from quant.portfolio import Portfolio
from quant.logging_backtest import logger
```
* 策略的主类：
```python
class MyStrategy(Strategy):  # set your strategy's name
    def __init__(self, market_event):
        super().__init__(market_event)

    def prenext(self):
        """这里查看框架中传过来的各个参数"""
        pass

    def next(self):
        """
        这里编辑策略，可以参考 tests/my_strategy.py 里的此部分，
        具体可用的指标可以查看 quant/indicator.py 或入门篇的指标部分,
        买卖操作可以查看 quant/strategy.py 中的 Strategy 类或入门篇的策略部分
        """
        pass
```
* 设置运行策略所需的数据和参数，运行框架
```python
trade = Quant()
data = CSV(
    datapath='/xx/yourdata.csv',
    instrument='IF',  # set your data's name
    startdate='2013-01-04',  # set your date
    enddate='2017-12-11')
data_list = [data]
portfolio = Portfolio
strategy = MyStrategy

trade.set_backtest(data_list, [strategy], portfolio)
trade.set_commission(commission=0.0003, margin=0.08, units=300, lots=1, instrument='IF')  # set your parameters
trade.set_cash(500000)
trade.set_notify()
trade.run()
logger.debug(trade.get_trade_log('IF'))
trade.plot(instrument='IF')
```


## 入门篇
### 指标
指标基类文件(quant/indicator.py)中主要包括默认定义好的一些指标。
如简单移动平均、开盘价、最高价、最低价、收盘价等。
自定义指标可直接在 Indicator 类中添加自定义函数。
```python
class Indicator(IndicatorBase):
    """自定义指标，如简单移动平均指标"""

    def __init__(self, market_event):
        super().__init__(market_event)
        self.SMA = self.simple_moving_average
        self.fill = market_event.fill
```
框架中的数据传递主要依靠 event事件。market_event 即市场事件，包含了几乎所有的信息，如每日的行情、策略中设置的参数等等。


```python

```
```python

```
默认定义好的指标，比如收盘价：
```python
def close(self, period=1) -> list:
    """
    close(1)[0] 表示当前周期的close
    close(2)[0] 表示上一周期的close
    """
    close = self.get_basic_data(period, ohlc='close')
    return close
```


```python
class Indicator(IndicatorBase):
    """自定义指标，如简单移动平均指标"""

    def __init__(self, market_event):
        super().__init__(market_event)
        self.SMA = self.simple_moving_average
        self.fill = market_event.fill

    def simple_moving_average(self, period, index=-1):

    def open(self, period=1):

    def high(self, period=1):

    def low(self, period=1):

    def close(self, period=1) -> list:
        """
        close(1)[0] 表示当前周期的close
        close(2)[0] 表示上一周期的close
        """
        close = self.get_basic_data(period, ohlc='close')
        return close

    def average_true_range(self, period: int) -> float:
        """period个周期内的平均真实波幅，一般称为ATR"""
        if not isinstance(period, int):
            logger.info('period must be int, please input int')
        high = self.high(period)  # type：numpy.ndarray，可以直接进行列表计算
        low = self.low(period)  # type：numpy.ndarray
        last_open = self.open(period + 1)[:-1]  # type：numpy.ndarray
        high_low = high - low  # type：numpy.ndarray
        high_last_open = high - last_open
        last_open_low = last_open - low
        true_range = [max(high_low[i], high_last_open[i], last_open_low[i]) for i in range(period)]
        average_true_range = talib.SMA(np.array(true_range), period)
        return average_true_range[-1]

    def money(self):
        return self.fill.balance[-1]

    def units(self):
        return self.market_event.units

    def position(self):
        return self.fill.position[-1]

    def max_high(self, period: int, index=0):
        """
        获取 period 个周期内的最高价，
        1 表示当前周期，2 表示上一周期到当前周期，类推，
        index 为 0 表示 period - 1 日前到当日的最高价，即 period 个周期内的最高价，
        index 为 1 表示 period 日前到昨日的最高价，也是 period 个周期内的最高价，
        index 是为比较函数 cross_up 和 cross_down 设置的
        """
        if index not in [0, 1]:
            logger.warning('index must be 0 or 1, please choose the right index')
            logger.info('index set to 0 by default')
            index = 0
        if not index:
            high = self.get_basic_data(period, ohlc='high')
        if index == 1:
            high = self.get_basic_data(period + 1, ohlc='high')[:-1]
        return max(high)

    def min_low(self, period: int, index=0):
        """
        获取 period 个周期内的最低价，
        index 为 0 表示 period + 1 日前到当日的最低价，
        index 为 1 表示 period + 2 日前到昨日的最低价，
        +2 是因为要与上一个 index 的周期相同，便于比较，
        用于计算 cross up 和 cross down
        """
        if index not in [0, 1]:
            logger.warning('index must be 0 or 1, please choose the right index')
            logger.info('index set to 0 by default')
            index = 0
        if not index:
            low = self.get_basic_data(period, ohlc='low')
        if index == 1:
            low = self.get_basic_data(period + 1, ohlc='low')[:-1]
        return min(low)

    def is_last_bk(self):
        """是否已买入开仓"""
        position = self.position()
        if position > 0:
            return 1
        else:
            return 0

    def is_last_sk(self):
        """是否已卖出开仓"""
        position = self.position()
        if position < 0:
            return 1
        else:
            return 0

    def cross_up(self, arg1: list, arg2: list) -> True or False:
        """
        暂时只比较两个值，理论上有中间多个值都相等再穿越的情况，
        即一条线从下方与另一条线重合再向上穿越，
        arg1[0]、arg2[0] 表示前一周期的数据，
        arg1[1]、arg2[1] 表示当前周期的数据，
        """
        if (isinstance(arg1, list) and isinstance(
                arg2, list) and len(arg1) == len(arg2) == 2):
                if arg1[0] < arg2[0] and arg1[1] > arg2[1]:
                    return True
                else:
                    return False
        else:
            return False

    def cross_down(self, arg1: list, arg2: list) -> True or False:
        """
        暂时只比较两个值，理论上有中间多个值都相等再穿越的情况，
        即一条线从上方与另一条线重合再向下穿越
        arg1[0]、arg2[0] 表示前一周期的数据，
        arg1[1]、arg2[1] 表示当前周期的数据，
        """
        if (isinstance(arg1, list) and isinstance(
                arg2, list) and len(arg1) == len(arg2) == 2):
                if arg1[0] > arg2[0] and arg1[1] < arg2[1]:
                    return True
                else:
                    return False
        else:
            return False
```

### 策略
策略基类文件（quant/strategy.py）中主要包括根据策略的择时情况进行的买卖操作。
即买平后再买开、卖平后再卖开、买入和卖出。
```python
class Strategy(StrategyBase):
    def __init__(self, market_event):

    def buy_even_and_open(self,
                          lots,
                          instrument=None,
                          price=None,
                          take_profit=None,
                          stop_loss=None,
                          trailing_stop=None):

    def sell_even_and_open(self,
                           lots,
                           instrument=None,
                           price=None,
                           take_profit=None,
                           stop_loss=None,
                           trailing_stop=None):

    def buy(self,
            lots,
            instrument=None,
            price=None,
            take_profit=None,
            stop_loss=None,
            trailing_stop=None):

    def sell(self,
             lots,
             instrument=None,
             price=None,
             take_profit=None,
             stop_loss=None,
             trailing_stop=None):

```

## 高级篇

##

## 附录




