# coding:utf-8
from queue import Queue, Empty
from threading import Thread, Timer
from logging_backtest import logger


class EventEngine(object):
    """
    事件驱动引擎
    """

    def __init__(self):
        """初始化事件引擎"""
        # 事件队列
        self.__event_queue = Queue()
        # 事件引擎开关
        self.__active = False
        # 事件处理线程
        self.__thread = Thread(target=self.__run)
        # 这里的__handlers是一个字典，用来保存对应的事件的响应函数
        # 其中每个键对应的值是一个列表，列表中保存了对该事件监听的响应函数，一对多
        self.__handlers = {}

    def __run(self):
        """引擎运行"""
        while self.__active is True:
            try:
                # 获取事件的阻塞时间设为1秒
                event = self.__event_queue.get(block=True, timeout=1)
                self.__process(event)
            except Empty:
                pass

    def __process(self, event):
        """处理事件"""
        # 检查是否存在对该事件进行监听的处理函数
        if event.type_ in self.__handlers:
            # 若存在，则按顺序将事件传递给处理函数执行
            for handler in self.__handlers[event.type_]:
                handler(event)

    def start(self):
        """启动"""
        # 将事件管理器设为启动
        self.__active = True
        # 启动事件处理线程
        self.__thread.start()

    def stop(self):
        """停止"""
        # 将事件管理器设为停止
        self.__active = False
        # 等待事件处理线程退出
        self.__thread.join()

    def bind(self, type_, handler):
        """绑定事件和监听器处理函数"""
        # 尝试获取该事件类型对应的处理器列表，若无则创建
        try:
            handler_list = self.__handlers[type_]
        except KeyError:
            handler_list = []

        self.__handlers[type_] = handler_list

        # 若要注册的处理器不在该事件的处理器列表中，则注册该事件
        if handler not in handler_list:
            handler_list.append(handler)

    def unbind(self, type_, handler):
        """解绑事件和监听器处理函数"""
        # 尝试获取该事件类型对应的处理器列表，若无则忽略该次请求
        try:
            handler_list = self.__handlers[type_]
        except KeyError:
            handler_list = []

        # 若要解绑的处理器在该事件的处理器列表中，则解绑
        if handler in handler_list:
            handler_list.remove(handler)

        # 如果处理器列表为空，则移除该事件类型
        if not handler_list:
            del self.__handlers[type_]

    def send_event(self, event):
        """发送事件，将事件存入事件列表"""
        self.__event_queue.put(event)


class Event(object):
    """事件对象"""
    def __init__(self, type_=None):
        self.type_ = type_  # 事件类型
        self.dict = {}  # 用于保存具体的事件数据的字典


# 测试部分------------------
STRATEGY = 'A new strategy'


class MultiStrategy(object):
    def __init__(self, event_engine):
        self.__event_engine = event_engine

    def create_new_strategy(self):
        event = Event(type_=STRATEGY)
        event.dict['action'] = 'buy buy buy'
        self.__event_engine.send_event(event)
        logger.info('产生新的策略')


class OrderListener(object):
    def __init__(self, order_id):
        self.__order_id = order_id

    def order(self, event):
        logger.info('{}, 有新的交易待处理'.format(self.__order_id))
        logger.info('this event says {}'.format(event.dict['action']))


def test():
    """测试函数"""
    # 实例化两个交易监听器
    order1 = OrderListener('1097')
    order2 = OrderListener('1098')

    event_engine = EventEngine()

    # 绑定事件和监听器处理函数，启动引擎
    event_engine.bind(STRATEGY, order1.order)
    event_engine.bind(STRATEGY, order2.order)
    event_engine.start()

    # 设定事件源，执行事件源
    strategys = MultiStrategy(event_engine)
    timer = Timer(2, strategys.create_new_strategy)
    timer.start()


if __name__ == '__main__':
    test()