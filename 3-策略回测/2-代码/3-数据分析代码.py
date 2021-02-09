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


class DataAnalysis:

    def __init__(self):
            """"""
            self.symbol = ""
            self.exchange = None
            self.interval = None
            self.start = None
            self.end = None
            self.rate = 0.0

            self.window_volatility = 20
            self.window_index = 20

            self.original = pd.DataFrame()

            self.index_1to1 = []
            self.index_2to1 = []
            self.index_2to2 = []   
            self.index_3to1 = []
            self.index_4to1 = []
            self.intervals = []

            self.results = {}

    def load_history(
        self,
        symbol: str, 
        exchange: Exchange, 
        interval: Interval, 
        start: datetime, 
        end: datetime,
        rate: float = 0.0,
        index_1to1: list = None,
        index_2to1: list = None,
        index_2to2: list = None,
        index_3to1: list = None,
        index_4to1: list = None,
        window_index: int = 20,
        window_volatility: int = 20,
    ):
        """""" 
        self.output("开始加载历史数据")

        self.window_volatility = window_volatility
        self.window_index = window_index
        self.rate = rate
        self.index_1to1 = index_1to1
        self.index_2to2 = index_2to2
        self.index_3to1 = index_3to1
        self.index_2to1 = index_2to1
        self.index_4to1 = index_4to1

        # Load history data from database  
        bars = database_manager.load_bar_data(    
            symbol=symbol, 
            exchange=exchange, 
            interval=interval, 
            start=start, 
            end=end
        )

        self.output(f"历史数据加载完成，数据量：{len(bars)}")
        
        # Generate history data in DataFrame
        t = []
        o = []
        h = []
        l = []
        c = []
        v = []

        for bar in bars:
            time = bar.datetime
            open_price = bar.open_price
            high_price = bar.high_price
            low_price = bar.low_price
            close_price = bar.close_price
            volume = bar.volume
            
            t.append(time)
            o.append(open_price)
            h.append(high_price)
            l.append(low_price)
            c.append(close_price)  
            v.append(volume)

        self.original["open"] = o
        self.original["high"] = h
        self.original["low"] = l
        self.original["close"] = c
        self.original["volume"] = v
        self.original.index = t

        # 将读取的数据写入excel表格
        # original['datetime'] = original['datetime'].apply(lambda a: pd.to_datetime(a).date()) 
        # excel_filelocation = Path('/Users/huangning/Library/Mobile Documents/com~apple~CloudDocs/CTA策略/CTA/3-策略回测/2-代码/rb2010数据分析表格.xlsx')
        # writer = pd.ExcelWriter(excel_filelocation, engine='xlsxwriter', options={'remove_timezone': True})
        # original.to_excel(writer, engine='xlsxwriter', sheet_name='rb2010')
        # writer.save()
        # writer.close()

    def base_analysis(self, df: DataFrame = None):
        """"""
        if df is None:
            df = self.original
       
        if df is None:
            self.output("数据为空，请输入数据")

        close_price = df["close"]

        self.output("第一步:画出行情图，检查数据断点")
        
        close_price.plot(figsize=(20, 8), title="close_price")
        plt.show()
    
        self.random_test(close_price)
        self.stability_test(close_price)
        self.autocorrelation_test(close_price)

        self.relative_volatility_analysis(df)
        self.growth_analysis(df)

        self.calculate_index(df)

        return df

    def random_test(self, close_price):
        """
        白噪声检验
        若p值>0.05，证明数据具有纯随机性：不具备某些数据特征，没有数据分析意义；
        若p值<0.05，证明数据不具有纯随机性：具备某些数据特性，进行数据分析有利于开发出适应其统计规律的交易策略。
        """
        acorr_result = acorr_ljungbox(close_price, lags=1)
        p_value = acorr_result[1]
        if p_value < 0.05:
            self.output("第二步：随机性检验：非纯随机性")
        else:
            self.output("第二步：随机性检验：纯随机性")
        self.output(f"白噪声检验结果:{acorr_result}\n")

    def stability_test(self, close_price):
        """
        平稳性检验
        若ADF值>10% 统计量，说明原假设成立：存在单位根，时间序列不平稳；
        若ADF值<10% 统计量，说明原假设不成立：不存在单位根，时间序列平稳。
        """
        statitstic = ADF(close_price)
        t_s = statitstic[1]
        t_c = statitstic[4]["10%"]

        if t_s > t_c:
            self.output("第三步：平稳性检验：存在单位根，时间序列不平稳")
        else:
            self.output("第三步：平稳性检验：不存在单位根，时间序列平稳")

        self.output(f"ADF检验结果：{statitstic}\n")

    def autocorrelation_test(self, close_price):
        """
        自相关性检验
        自相关图：统计相关性总结了两个变量之间的关系强度，即描述了一个观测值与另一个观测值之间的自相关，包括直接和间接的相关性信息。
        这种关系的惯性将继续到之后的滞后值，随着效应被削弱而在某个点上缩小到没有。
        偏自相关图：偏自相关是剔除干扰后时间序列观察与先前时间步长时间序列观察之间关系的总结，即只描述观测值与其滞后之间的直接关系。
        可能超过k的滞后值不会再有相关性。
        """
        self.output("第四步：画出自相关性图，观察自相关特性")

        plot_acf(close_price, lags=60)
        plt.show()

        plot_pacf(close_price, lags=60).show()
        plt.show()

    def relative_volatility_analysis(self, df: DataFrame = None):
        """
        相对波动率
        调用talib库的ATR函数计算1分钟K线的绝对波动率；
        通过收盘价*手续费计算固定成本；
        相对波动率=绝对波动率-固定成本；
        对相对波动率进行画图：时间序列图和频率分布图；
        对相对波动率进行描述统计分析，得到平均数、中位数、偏度、峰度
        """
        self.output("第五步：相对波动率分析")

        df["volatility"] = talib.ATR(
            np.array(df['high']),
            np.array(df['low']),
            np.array(df['close']),
            self.window_volatility
            )

        df["fixed_cost"] = df["close"] * self.rate
        df["relative_vol"] = df["volatility"] - df["fixed_cost"]

        df["relative_vol"].plot(figsize=(20, 6), title="relative volatility")
        plt.show()

        df["relative_vol"].hist(bins=200, figsize=(20, 6), grid=False)
        plt.show()

        self.statitstic_info(df["relative_vol"])

    def statitstic_info(self, df):
        """
        描述统计信息
        """
        mean = round(df.mean(), 4)
        median = round(df.median(), 4)    
        self.output(f"样本平均数：{mean}, 中位数: {median}")

        skew = round(df.skew(), 4)
        kurt = round(df.kurt(), 4)

        if skew == 0:
            skew_attribute = "对称分布"
        elif skew > 0:
            skew_attribute = "分布偏左"
        else:
            skew_attribute = "分布偏右"

        if kurt == 0:
            kurt_attribute = "正态分布"
        elif kurt > 0:
            kurt_attribute = "分布陡峭"
        else:
            kurt_attribute = "分布平缓"

        self.output(f"偏度为：{skew}，属于{skew_attribute}；峰度为：{kurt}，属于{kurt_attribute}\n")

    def growth_analysis(self, df: DataFrame = None):
        """
        百分比K线变化率
        计算百分比变化率 = 100*（收盘价- 上一根收盘价）/上一根收盘价；
        对变化率进行画图：时间序列图和频率分布图；
        对变化率进行描述统计分析，得到平均数、中位数、偏度、峰度。
        """
        self.output("第六步：变化率分析")
        df["pre_close"] = df["close"].shift(1).fillna(0)
        df["g%"] = 100 * (df["close"] - df["pre_close"]) / df["close"]

        df["g%"].plot(figsize=(20, 6), title="growth", ylim=(-5, 5))
        plt.show()

        df["g%"].hist(bins=200, figsize=(20, 6), grid=False)
        plt.show()

        self.statitstic_info(df["g%"])

    def calculate_index(self, df: DataFrame = None):
        """"""
        self.output("第七步：计算相关技术指标，返回DataFrame\n")

        if self.index_1to1:
            for i in self.index_1to1:
                func = getattr(talib, i)
                df[i] = func(
                    np.array(df["close"]), 
                    self.window_index
                )

        if self.index_3to1:
            for i in self.index_3to1:
                func = getattr(talib, i)
                df[i] = func(        
                    np.array(df["high"]),
                    np.array(df["low"]),
                    np.array(df["close"]),
                    self.window_index
                )
                
        if self.index_2to2:
            for i in self.index_2to2:
                func = getattr(talib, i)
                result_down, result_up = func(
                    np.array(df["high"]),
                    np.array(df["low"]),
                    self.window_index
                )
                up = i + "_UP"
                down = i + "_DOWN"
                df[up] = result_up
                df[down] = result_down
        
        if self.index_2to1:
            for i in self.index_2to1:
                func = getattr(talib, i)
                df[i] = func(
                    np.array(df["high"]),
                    np.array(df["low"]),
                    self.window_index
                )

        if self.index_4to1:
            for i in self.index_4to1:
                func = getattr(talib, i)
                df[i] = func(  
                    np.array(df["open"]),      
                    np.array(df["high"]),
                    np.array(df["low"]),
                    np.array(df["close"]),
                )
        return df

    def multi_time_frame_analysis(self, intervals: list = None, df: DataFrame = None):
        """"""
        if not intervals:
            self.output("请输入K线合成周期")
            return

        if df is None:
            df = self.original

        if df is None:
            self.output("请先加载数据")
            return

        for interval in intervals: 
            self.output("------------------------------------------------")  
            self.output(f"合成{interval}周期K先并开始数据分析")
              
            data = pd.DataFrame()
            data["open"] = df["open"].resample(interval, how="first")
            data["high"] = df["high"].resample(interval, how="max")
            data["low"] = df["low"].resample(interval, how="min")
            data["close"] = df["close"].resample(interval, how="last")
            data["volume"] = df["volume"].resample(interval, how="sum")

            result = self.base_analysis(data)
            self.results[interval] = result

    def show_chart(self, data, boll_wide):
        """"""      
        data["boll_up"] = data["SMA"] + data["STDDEV"] * boll_wide
        data["boll_down"] = data["SMA"] - data["STDDEV"] * boll_wide

        up_signal = []
        down_signal = []
        len_data = len(data["close"]) 
        for i in range(1, len_data):
            if data.iloc[i]["close"] > data.iloc[i]["boll_up"]and data.iloc[i-1]["close"] < data.iloc[i - 1]["boll_up"]:
                up_signal.append(i)

            elif data.iloc[i]["close"] < data.iloc[i]["boll_down"] and data.iloc[i-1]["close"] > data.iloc[i - 1]["boll_down"]:
                down_signal.append(i)

        fig = plt.figure(figsize=(20, 8))
        close = data["close"]
        plt.plot(close, lw=1)
        plt.plot(close, '^', markersize=5, color='r', label='UP signal', markevery=up_signal)
        plt.plot(close, 'v', markersize=5, color='g', label='DOWN signal', markevery=down_signal)
        plt.plot(data["boll_up"], lw=0.5, color="r")
        plt.plot(data["boll_down"], lw=0.5, color="g")
        plt.legend()
        plt.show()

        data["ATR"].plot(figsize=(20, 3), title="ATR")
        plt.show()

    def output(self, msg):
        """
        Output message of backtesting engine.
        """
        print(f"{datetime.now()}\t{msg}")

#%%
herramiento = DataAnalysis()
herramiento.load_history(
    symbol="rb2010",
    exchange=Exchange.SHFE,
    interval=Interval.MINUTE,
    start=datetime(2020, 1, 1),
    end=datetime(2020, 12, 31),
    rate=1/10000,
    index_1to1 = ["STDDEV","SMA"],
    index_2to1 = ["AROONOSC"],
    index_2to2 = ["AROON"],
    index_3to1 = ["ATR","ADX","CCI"],
    index_4to1 = ["BOP"],
    window_index=30
)
herramiento.base_analysis(herramiento.original)
# %%
