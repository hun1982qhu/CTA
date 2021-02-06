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
import xlsxwriter。
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
def random_test(close_price):
    """
    白噪声检验
    若p值>0.05，证明数据具有纯随机性：不具备某些数据特征，没有数据分析意义；
    若p值<0.05，证明数据不具有纯随机性：具备某些数据特性，进行数据分析有利于开发出适应其统计规律的交易策略。
    """
    acorr_result = acorr_ljungbox(close_price, lags=1)
    p_value = acorr_result[1]
    if p_value < 0.05:
        output("第二步：随机性检验：非纯随机性")
    else:
        output("第二步：随机性检验：纯随机性")
    output(f"白噪声检验结果:{acorr_result}\n")

random_test(original['close'])

#%%
def stability_test(close_price):
    """
    平稳性检验
    若ADF值>10% 统计量，说明原假设成立：存在单位根，时间序列不平稳；
    若ADF值<10% 统计量，说明原假设不成立：不存在单位根，时间序列平稳。
    """
    statitstic = ADF(close_price)
    t_s = statitstic[1]
    t_c = statitstic[4]["10%"]

    if t_s > t_c:
        output("第三步：平稳性检验：存在单位根，时间序列不平稳")
    else:
        output("第三步：平稳性检验：不存在单位根，时间序列平稳")

    output(f"ADF检验结果：{statitstic}\n")

stability_test(original['close'])

#%%
def autocorrelation_test(close_price):
    """
    自相关性检验
    自相关图：统计相关性总结了两个变量之间的关系强度，即描述了一个观测值与另一个观测值之间的自相关，包括直接和间接的相关性信息。
    这种关系的惯性将继续到之后的滞后值，随着效应被削弱而在某个点上缩小到没有。
    偏自相关图：偏自相关是剔除干扰后时间序列观察与先前时间步长时间序列观察之间关系的总结，即只描述观测值与其滞后之间的直接关系。
    可能超过k的滞后值不会再有相关性。
    """
    output("第四步：画出自相关性图，观察自相关特性")

    plot_acf(close_price, lags=60)
    plt.show()

    plot_pacf(close_price, lags=60).show()
    plt.show()

autocorrelation_test(original['close'])
#%%
# print(original.skew())
# print(round(original.skew(), 4))
print(original.kurt())

#%%
def statitstic_info(df, n):
    """
    描述统计信息
    """
    mean = round(df.mean(), 4)
    median = round(df.median(), 4)    
    output(f"样本平均数：{mean}, 中位数: {median}")

    skew = round(df.skew(), 4)
    kurt = round(df.kurt(), 4)

    if skew[n] == 0:
        skew_attribute = "对称分布"
    elif skew[n] > 0:
        skew_attribute = "分布偏左"
    else:
        skew_attribute = "分布偏右"

    if kurt[n] == 0:
        kurt_attribute = "正态分布"
    elif kurt[n] > 0:
        kurt_attribute = "分布陡峭"
    else:
        kurt_attribute = "分布平缓"

    output(f"偏度为：{skew[n]}，属于{skew_attribute}；峰度为：{kurt[n]}，属于{kurt_attribute}\n")

statitstic_info(original, 3)

#%%
def relative_volatility_analysis(df: DataFrame = None):
    """
    相对波动率
    调用talib库的ATR函数计算1分钟K线的绝对波动率；
    通过收盘价*手续费计算固定成本；
    相对波动率=绝对波动率-固定成本；
    对相对波动率进行画图：时间序列图和频率分布图；
    对相对波动率进行描述统计分析，得到平均数、中位数、偏度、峰度
    """
    output("第五步：相对波动率分析")
    df["volatility"] = talib.ATR(
        np.array(df['high']), 
        np.array(df['low']), 
        np.array(df['close']), 
        14) # self.window_volatility
    
    df["fixed_cost"] = df["close"] * 0.2  # self.rate
    df["relative_vol"] = df["volatility"] - df["fixed_cost"]

    df["relative_vol"].plot(figsize=(20, 6), title="relative volatility")
    plt.show()

    df["relative_vol"].hist(bins=200, figsize=(20, 6), grid=False)
    plt.show()

    statitstic_info(df, 6)

relative_volatility_analysis(original)

# %%
def growth_analysis(df: DataFrame = None):
    """
    百分比K线变化率
    计算百分比变化率 = 100*（收盘价- 上一根收盘价）/上一根收盘价；
    对变化率进行画图：时间序列图和频率分布图；
    对变化率进行描述统计分析，得到平均数、中位数、偏度、峰度。
    """
    output("第六步：变化率分析")
    df["pre_close"] = df["close"].shift(1).fillna(0)
    df["g%"] = 100 * (df["close"] - df["pre_close"]) / df["close"]

    df["g%"].plot(figsize=(20, 6), title="growth", ylim=(-5, 5))
    plt.show()

    df["g%"].hist(bins=200, figsize=(20, 6), grid=False)
    plt.show()

    statitstic_info(df, 7)
    
growth_analysis(original)
# %%
