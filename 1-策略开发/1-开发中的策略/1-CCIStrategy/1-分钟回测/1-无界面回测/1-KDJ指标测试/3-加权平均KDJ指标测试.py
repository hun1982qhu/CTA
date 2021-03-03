#%%
from typing import Any, Callable
from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager,
    TradeData,
    StopOrder,
    OrderData
)
from vnpy.app.cta_strategy.base import StopOrderStatus, BacktestingMode
from vnpy.app.cta_strategy.backtestingHN import BacktestingEngine, OptimizationSetting
from vnpy.trader.object import BarData, TickData
from vnpy.trader.constant import Interval, Offset, Direction, Exchange, Status
import numpy as np
import pandas as pd
from datetime import time as time1
from datetime import datetime
import time
import talib
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import style
mpl.rcParams['font.family'] = 'serif'  # 解决一些字体显示乱码的问题

style.use('ggplot')
import seaborn as sns

sns.set()

#%%
class CCIStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"

    bar_window_length = 3
    fixed_size = 10
    pricetick_multilplier = 7
    fastk_period = 9
    slowk_period = 5
    slowk_matype = 0
    slowd_period = 5
    slowd_matype = 0
    
    k1 = 0
    k2 = 0
    d1 = 0
    d2 = 0

    parameters = [
        "bar_window_length",
        "fixed_size",
        "pricetick_multilplier",
        "fastk_period",
        "slowk_period",
        "slowk_matype",
        "slowd_period",
        "slowd_matype"
    ]

    variables = [
        "k1",
        "k2",
        "d1",
        "d2"
    ]

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = XminBarGenerator(self.on_bar, self.bar_window_length, self.on_Xmin_bar)
        self.am = NewArrayManager()

        self.count = 0

    def on_init(self):
        """"""
        self.write_log("策略初始化")
        self.load_bar(1)

    def on_start(self):
        """"""
        self.write_log("策略启动")

    def on_stop(self):
        """"""
        self.write_log("策略停止")
        print("策略停止")
        
    def on_tick(self, tick: TickData):
        """"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """"""
        self.bg.update_bar(bar)
        
    def on_Xmin_bar(self, bar: BarData):
        """"""
        am = self.am

        am.update_bar(bar)
        if not am.inited:
            return

        # if not am.kdj_inited:
        #     return

        # self.count += 1
        # if self.count == 1:
            # print(am.kdj_weighted(9, True))

        self.slowk, self.slowd, self.slowj = am.kdj_weighted(self.fastk_period, array=True)
        print(self.slowk)
        print(len(self.slowk))

        # self.slowk, self.slowd, self.slowj = am.kdj(
        #     self.fastk_period,
        #     self.slowk_period,
        #     self.slowk_matype,
        #     self.slowd_period,
        #     self.slowd_matype,
        #     array=True
        #     )

        # print(self.slowk)

        # self.slowk, self.slowd, self.slowj = am.kdjs(
        #     9,
        #     array=True
        #     )    
       
    def on_stop_order(self, stop_order: StopOrder):
        """"""

    def on_order(self, order):
        """"""

class NewArrayManager(ArrayManager):
    """"""
    def __init__(self, size=100):
        """"""
        super().__init__(size)
        
        self.slowk = np.array([50, 50])
        self.slowd = np.array([50, 50])
        self.slowj = np.array([50, 50])

        self.K = 50
        self.D = 50
        self.J = 50

        self.kdj_count = 0
        self.kdj_inited = False
        self.kdj_size = 2
        
    def kdj_weighted(
        self,
        fastk_period, 
        array=False
        ):
        """"""

        high_array_kdj = self.high[-fastk_period:]
        low_array_kdj = self.low[-fastk_period:]
        close_array_kdj = self.close[-fastk_period:]

        volume_array_kdj = self.volume[-fastk_period:]
        total_volume = volume_array_kdj.sum()
        volume_array_kdj_wa = volume_array_kdj/total_volume

        high_array_kdj_wa = np.multiply(high_array_kdj, volume_array_kdj_wa)
        low_array_kdj_wa = np.multiply(low_array_kdj, volume_array_kdj_wa)
        close_array_kdj_wa = np.multiply(close_array_kdj, volume_array_kdj_wa)

        H = high_array_kdj_wa.mean()
        L = low_array_kdj_wa.mean()
        C = close_array_kdj_wa.mean()
        RSV = (C-L)*100/(H-L)

        # 无第1日K值，设为50
        if self.K == 50:
            self.K = self.K*2/3 + RSV*1/3
        else:
            self.K = self.K*2/3 + RSV*1/3
        
        # 无第1日D值，设为50
        if self.D == 50:
            self.D = self.D*2/3 + self.K*1/3
        else:
            self.D = self.D*2/3 + self.K*1/3 

        self.J = 3 * self.K - 2 * self.D

        self.slowk[:-1] = self.slowk[1:]
        self.slowd[:-1] = self.slowd[1:]
        self.slowj[:-1] = self.slowj[1:]

        self.slowk[-1] = self.K
        self.slowd[-1] = self.D
        self.slowj[-1] = self.J

        if array:
            return self.slowk, self.slowd, self.slowj
        return self.slowk[-1], self.slowd[-1], self.slowj[-1]
        
    def kdj(
        self, 
        fastk_period, 
        slowk_period, 
        slowk_matype, 
        slowd_period,
        slowd_matype, 
        array=False
        ):
        """"""
        slowk, slowd, = talib.STOCH(self.high, self.low, self.close, fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)
        # 求出J值，J = (3 * D) - (2 * K)
        slowj = list(map(lambda x, y: 3*x - 2*y, slowk, slowd))
        if array:
            return slowk, slowd, slowj
        return slowk[-1], slowd[-1], slowj[-1]

    def kdjs(self, n, array=False):
        """"""
        slowk, slowd = talib.STOCH(self.high, self.low, self.close, n, 3, 0, 3, 0)
        slowj = list(map(lambda x, y: 3*x - 2*y, slowk, slowd))
        if array:
            return slowk, slowd, slowj
        return slowk[-1], slowd[-1], slowj[-1]       


class XminBarGenerator(BarGenerator):
    def __init__(
        self,
        on_bar: Callable,
        window: int = 0,
        on_window_bar: Callable = None,
        interval: Interval = Interval.MINUTE
    ):
        super().__init__(on_bar, window, on_window_bar, interval)
    
    def update_bar(self, bar: BarData) ->None:
        """
        Update 1 minute bar into generator
        """
        # and (bar.exchange in [Exchange.SHFE, Exchange.DCE, Exchange.CZCE])
        # print(f"bar.datetime.time:{bar.datetime.time()}")
        # If not inited, creaate window bar object
        if not self.window_bar:
            # Generate timestamp for bar data
            if self.interval == Interval.MINUTE:
                dt = bar.datetime.replace(second=0, microsecond=0)
            else:
                dt = bar.datetime.replace(minute=0, second=0, microsecond=0)

            self.window_bar = BarData(
                symbol=bar.symbol,
                exchange=bar.exchange,
                datetime=dt,
                gateway_name=bar.gateway_name,
                open_price=bar.open_price,
                high_price=bar.high_price,
                low_price=bar.low_price
            )
        # Otherwise, update high/low price into window bar
        else:
            self.window_bar.high_price = max(
                self.window_bar.high_price, bar.high_price)
            self.window_bar.low_price = min(
                self.window_bar.low_price, bar.low_price)

        # Update close price/volume into window bar
        self.window_bar.close_price = bar.close_price
        self.window_bar.volume += int(bar.volume)
        self.window_bar.open_interest = bar.open_interest

        # Check if window bar completed
        finished = False

        if self.interval == Interval.MINUTE:
            # x-minute bar
            # if not (bar.datetime.minute + 1) % self.window:
            #     finished = True
            
            self.interval_count += 1

            if not self.interval_count % self.window:
                finished = True
                self.interval_count = 0

            elif bar.datetime.time() in [time1(10, 14), time1(11, 29), time1(14, 59), time1(22, 59)]:
                if bar.exchange in [Exchange.SHFE, Exchange.DCE, Exchange.CZCE]:
                    finished = True
                    self.interval_count = 0

        elif self.interval == Interval.HOUR:
            if self.last_bar:
                new_hour = bar.datetime.hour != self.last_bar.datetime.hour
                last_minute = bar.datetime.minute == 59
                not_first = self.window_bar.datetime != bar.datetime

                # To filter duplicate hour bar finished condition
                if (new_hour or last_minute) and not_first:
                    # 1-hour bar
                    if self.window == 1:
                        finished = True
                    # x-hour bar
                    else:
                        self.interval_count += 1

                        if not self.interval_count % self.window:
                            finished = True
                            self.interval_count = 0

        if finished:
            self.on_window_bar(self.window_bar)
            self.window_bar = None

        # Cache last bar object
        self.last_bar = bar
  
#%%
start1 = time.time()
engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="rb2010.SHFE",
    interval="1m",
    start=datetime(2019, 10, 15),
    end=datetime(2020,10,15),
    rate=0.0001,
    slippage=2,
    size=10,
    pricetick=1,
    capital=1_000_000,
    mode=BacktestingMode.BAR
)
engine.add_strategy(CCIStrategy, {})
#%%
start2 = time.time()
engine.load_data()
end2 = time.time()
print(f"加载数据所需时长: {(end2-start2)} Seconds")
#%%
engine.run_backtesting()
#%%
engine.calculate_result()
engine.calculate_statistics()
# 待测试的代码
end1 = time.time()
print(f"单次回测运行时长: {(end1-start1)} Seconds")
engine.show_chart()
#%%
# setting = OptimizationSetting()
# setting.set_target("end_balance")
# setting.add_parameter("bar_window_length", 1, 20, 1)
# setting.add_parameter("cci_window", 3, 10, 1)
# setting.add_parameter("fixed_size", 1, 1, 1)
# setting.add_parameter("sell_multipliaer", 0.80, 0.99, 0.01)
# setting.add_parameter("cover_multiplier", 1.01, 1.20, 0.01)
# setting.add_parameter("pricetick_multiplier", 1, 5, 1)
#%%
# engine.run_optimization(setting, output=True)