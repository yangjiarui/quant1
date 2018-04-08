# coding=utf-8
import pandas as pd
from abc import ABCMeta, abstractmethod
from datetime import datetime
import csv
from event import events, MarketEvent


class DataHandler(ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    def load_data(self):
        pass
        
    def start(self):
        pass
    
    def prenext(self):
        pass
    
    def next(self):
        events.put(MarketEvent(self))


class CSVDataReader(DataHandler):
    """识别csv数据中的数据，包括date、open、high、low、close"""

    def __init__(self, datapath, startdate=None, enddate=None):
        self.datapath = datapath
        self.startdate = startdate
        self.enddate = enddate

    def __set_date(self):
        """将日期转换成datetime对象"""
        if self.fromdate:
            self.fromdate = datetime.strptime(self.fromdate, "%Y-%m-%d")
        if self.todate:
            self.todate = datetime.strptime(self.todate, "%Y-%m-%d")

    def load_data(self):
        return csv.DictReader(open(self.datapath))
