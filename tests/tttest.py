from pprint import pprint
from copy import copy
import inspect

H_L = {'arg': ['high', 'low'], 'func': '-'}
abs1 = {'func': 'abs', 'arg': [{'arg': ['close1', 'high'], 'func': '-'}]}
abs2 = {'func': 'abs', 'arg': [{'arg': ['close1', 'low'], 'func': '-'}]}
tr = {'func': 'max', 'arg': [H_L, abs1, abs2]}
atr = {'func': 'ma', 'arg': [tr, 20]}
money_ = {'func': '*', 'arg': ['money', 0.01]}
unit_ = {'func': '*', 'arg': ['unit', atr]}
tc = {'func': 'int', 'arg': [{'func': '/', 'arg': [money_, unit_]}]}
mtc = {'func': '*', 'arg': [4, tc]}
hh = {'func': 'max_high', 'arg': ['high', 20]}
ll = {'func': 'min_low', 'arg': ['low', 20]}
crossup1 = {'func': 'crossup', 'arg': ['close', ll]}
# ma5 = {'func': 'ma', 'arg': [atr, 5]}
# ma10 = {'func': 'ma', 'arg': [atr, 10]}
ma5 = {'func': 'ma', 'arg': ['close', 5]}
ma10 = {'func': 'ma', 'arg': ['close', 10]}

crossup2 = {'func': 'crossup', 'arg': [ma5, ma10]}
pprint(mtc)
pprint(crossup2)
pprint(atr)


class FindMaxPeriod(object):
    def __init__(self):
        self._period = []

    def find(self, dic):
        for key, value in dic.items():
            if key is 'func':
                pass
            if key is 'arg':  # value 是一个列表
                # print('lenth of value: {}'.format(value))
                pprint(value)
                for i in value:
                    print('i:', i)
                    if isinstance(i, int) or isinstance(i, float):
                        self._period.append(i)
                        print('append: {}'.format(i))
                        # continue
                    elif isinstance(i, dict):
                        self.find(i)  # 只要是字典，一定会返回一个值，否则报错
                        # continue
                    else:
                        self._period.append(0)
                        print('else: {}'.format(i))
        print(self._period)
        print('max(self._period): {}'.format(max(self._period)))
        return max(self._period)


c = FindMaxPeriod()
c.find(mtc)
print('---------------------------')
d = FindMaxPeriod()
d.find(crossup2)
print('---------------------------')
e = FindMaxPeriod()
e.find(atr)


# def v2():
#     print(inspect.stack()[1][3])


# def v1():
#     """返回函数名：v1"""
#     v2()


# v1()
