# coding:utf-8
from logging_backtest import logger


def dict_to_table(result_dict):
    # 计算传入字典的key的长度的最大值作为key展示列的宽度
    col_width_keys = max([len(key) for key in result_dict.keys()])
    # 计算传入字典的value的长度的最大值作为value展示列的宽度
    col_width_values = max([len(str(value)) for value in result_dict.values()])
    # 列表的头部和尾部用#---#展示
    header_footer = ('#--' +
                     (col_width_keys + col_width_values + 2) * '-' + '#')
    data_list = []
    for key, value in result_dict.items():
        data_list.append('| ' + '| '.join([
            '{:{}}'.format(key, col_width_keys), '{:{}}'.format(
                value, col_width_values)
        ]) + ' |\n')

    table_str = '{}\n{}{}'.format(header_footer, ''.join(data_list),
                                  header_footer)
    logger.info(table_str)


if __name__ == '__main__':
    result_dict = {
        'a': 212334523523543534,
        'basdfasdfasdfasdfsdssdf': 32432,
        'c': 23490,
        'ddsaf': 2324423,
        'ed': 31412
    }
    dict_to_table(result_dict)
