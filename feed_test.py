# coding:utf-8
from feedbase import CSVDataReader

datapath = '../IF_cleaned_data.csv'
IF = CSVDataReader(
    datapath=datapath,
    instrument='IF',
    startdate='2015-04-01',
    enddate='2015-04-05')


IF.preload()
data_list = [IF]
print(len(data_list))
print(data_list[0])
print(data_list)
