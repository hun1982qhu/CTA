#%%
from vnpy.trader.database import database_manager
from datetime import datetime
from vnpy.trader.constant import Exchange, Interval, Offset, Direction
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import adfuller as ADF
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import talib
import pandas as pd
from pandas import DataFrame
import numpy as np
from numpy import array
from pathlib import PosixPath,Path
import xlsxwriter
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import style
mpl.rcParams['font.family'] = 'serif'  # 解决一些字体显示乱码的问题

style.use('ggplot')
import seaborn as sns

sns.set()

def output(msg):
    """"""
    print(f"{datetime.now()}\t{msg}")

output("开始加载历史数据")
bars = database_manager.load_bar_data(
    symbol="rb2010", 
    exchange=Exchange.SHFE, 
    interval=Interval.MINUTE, 
    start=datetime(2020, 1, 1), 
    end=datetime(2020,12, 31)
    )
output(f"历史数据加载完成，数据量：{len(bars)}")

#%%
# Generate history data in DataFrame
t = []
o = []
h = []
l = []
c = []

for bar in bars:
    time = bar.datetime
    open_price = bar.open_price
    high_price = bar.high_price
    low_price = bar.low_price
    close_price = bar.close_price

    t.append(time)
    o.append(open_price)
    h.append(high_price)
    l.append(low_price)
    c.append(close_price)

original = pd.DataFrame()
original["open"] = o
original["high"] = h
original["low"] = l
original["close"] = c
original.index = t

# original['datetime'] = original['datetime'].apply(lambda a: pd.to_datetime(a).date()) 
# excel_filelocation = Path('/Users/huangning/Library/Mobile Documents/com~apple~CloudDocs/CTA策略/CTA/3-策略回测/2-代码/rb2010数据分析表格.xlsx')
# writer = pd.ExcelWriter(excel_filelocation, engine='xlsxwriter', options={'remove_timezone': True})
# original.to_excel(writer, engine='xlsxwriter', sheet_name='rb2010')
# writer.save()
# writer.close()

output("第一步:画出行情图，检查数据断点")
original["close"].plot(figsize=(20, 8), title="close_price")
plt.show()

#%%
print(np.array(original['high']))

print(type(np.array(original['high'])))
# %%
