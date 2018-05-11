# coding=utf-8
import logging
import sys
import logging.handlers

# 获取logger实例，空，则返回root logger
logger = logging.getLogger('backtest')
# 指定输出格式
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s in line %(lineno)d  |||| %(message)s')
# 日志保存到文件
filepath = 'backtest_error.log'
file_handler = logging.handlers.TimedRotatingFileHandler(
    filepath, when='midnight', interval=1, backupCount=10)
file_handler.setFormatter(formatter)
# 日志输出到控制台
console_handler = logging.StreamHandler(sys.stdout)
console_handler.formatter = formatter
logger.addHandler(file_handler)
logger.addHandler(console_handler)
# 指定输出级别
logger.setLevel(logging.INFO)
