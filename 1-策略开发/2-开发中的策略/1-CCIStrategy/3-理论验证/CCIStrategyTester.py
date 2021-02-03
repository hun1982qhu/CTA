#%%
from datetime import time
from typing import Any
from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager
)
from vnpy.trader.object import (BarData, TickData)

import rqdatac as rq 
from rqdatac import * 
rq.init('13581903798','hun829248')
import talib
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import style


style.use('ggplot')
import seaborn as sns

sns.set()

mpl.rcParams['font.sans-serif'] = ['Arial Unicode MS']
mpl.rcParams['axes.unicode_minus'] = False
#%%
data = get_price("RB2010", start_date="2020-01-01", end_date="2020-09-11", frequency='1m')
print(data)
#%%
data['close'].plot(figsize=(10, 6))
plt.show()
#%%
data['cci'] = talib.CCI(data['high'], data['low'], data['close'], timeperiod=14)
data['cci'].plot(figsize=(10, 6))
plt.axhline(100, color='r')
plt.axhline(-100, color='r')
plt.axhline(0, color='r')
plt.show()
#%%
data['cci_yd'] = data['cci'].shift(1)
data['cci_b_yd'] = data['cci'].shift(2)
print(data)
#%%
# over_bought = (data.loc['2020/1/2 9:10:00', 'cci'] >= cci_up_break)
# print(over_bought)
#%%
data['over_bought'] = (data['cci'] >= 100)
data['high_turning_cond1'] = (data['cci'] < data['cci_yd'])
data['high_turning_cond2'] = (data['cci_b_yd'] < data['cci_yd'])
data['over_sold'] = (data['cci'] <= -100)
data['low_turning_cond1'] = (data['cci'] > data['cci_yd'])
data['low_turning_cond2'] = (data['cci_b_yd'] > data['cci_yd'])
print(data)
#%%
data['position'] = np.where((data['over_bought']) & (data['high_turning_cond1']) & (data['high_turning_cond2']), -1, np.nan)  # 给空值是这个策略的重要一点，方便后面填充
data['position'] = np.where((data['over_sold']) & (data['low_turning_cond1']) & (data['low_turning_cond2']), 1, data['position'])
data['position'] = data['position'].ffill().fillna(0)
print(data['position'])
#%%
# 计算每日收益
data['return_dis'] = data['close'].pct_change()
# 计算策略每日收益率
data['return_strategy'] = data['return_dis'] * data['position']  # 此处不用加shift(1)，因为交易信号就是当天获得
# 计算累计收益
data['return_dis_cum'] = (data['return_dis'] + 1).cumprod()
# 计算策略累计收益
data['return_strategy_cum'] = (data['return_strategy'] + 1).cumprod()
#%%
data[['return_dis_cum', 'return_strategy_cum']].plot(figsize=(12, 6))
plt.title('螺纹钢 CCI策略收益图')
plt.legend(loc='upper left')
plt.show()
#%%
df_file = pd.ExcelWriter('数据.xls')
data.to_excel(df_file, '20190901-20200901')
df_file.save()
df_file.close()
# %%
