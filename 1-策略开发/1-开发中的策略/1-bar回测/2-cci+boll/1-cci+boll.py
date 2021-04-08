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
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
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
class CCIBollStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"

    bar_window_length1 = 5
    bar_window_length2 = 15
    cci_window = 20
    boll_window = 20
    boll_dev = 2.0
    pricetick_multilplier1 = 1
    pricetick_multilplier2 = 0
    fixed_size = 1

    cci = 0
    boll_up = 0
    boll_down = 0


    parameters = [
        "bar_window_length1",
        "bar_window_length2",
        "cci_window",
        "boll_window",
        "boll_dev",
        "pricetick_multilplier1",
        "pricetick_multilplier2",
        "fixed_size"
    ]

    variables = [
        "cci",
        "boll_up",
        "boll_down"
    ]

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg1 = XminBarGenerator(self.on_bar, self.bar_window_length1, self.on_Xmin1_bar)
        self.bg2 = XminBarGenerator(self.on_bar, self.bar_window_length2, self.on_Xmin2_bar)
        self.am1 = NewArrayManager()
        self.am2 = NewArrayManager()
        
        self.pricetick = self.get_pricetick()

        self.buy_vt_orderids = []
        self.sell_vt_orderids = []
        self.short_vt_orderids = []
        self.cover_vt_orderids = []

        self.buy_price = 0
        self.sell_price = 0
        self.short_price = 0
        self.cover_price = 0

    def on_init(self):
        """"""
        self.write_log("策略初始化")
        print("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """"""
        self.write_log("策略启动")
        print("策略启动")

    def on_stop(self):
        """"""
        self.write_log("策略停止")
        print("策略停止")
        
    def on_tick(self, tick: TickData):
        """"""
        self.bg1.update_tick(tick)

    def on_bar(self, bar: BarData):
        """"""
        self.bg1.update_bar(bar)
        self.bg2.update_bar(bar)

        if self.buy_vt_orderids:
            for vt_orderid in self.buy_vt_orderids:
                self.cancel_order(vt_orderid)
            self.buy_vt_orderids = self.buy(bar.close_price + self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)
            
        elif self.short_vt_orderids:
            for vt_orderid in self.short_vt_orderids:
                self.cancel_order(vt_orderid)
            self.short_vt_orderids = self.short(bar.close_price - self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)

        elif self.sell_vt_orderids:
            for vt_orderid in self.sell_vt_orderids:
                self.cancel_order(vt_orderid)
            self.sell_vt_orderids = self.sell(bar.close_price - self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)

        elif self.cover_vt_orderids:
            for vt_orderid in self.cover_vt_orderids:
                self.cancel_order(vt_orderid)
            self.cover_vt_orderids = self.cover(bar.close_price + self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)

    def on_Xmin1_bar(self, bar: BarData):
        """"""
        print(f"5minutebar.datetime:{bar.datetime}")
        am1 = self.am1
        am1.update_bar(bar)
        if not am1.inited:
            return
        
        self.boll_up, self.boll_down = am1.boll(self.boll_window, self.boll_dev)

        if self.pos == 0:
            if not self.buy_vt_orderids:
                if  self.cci > 0:
                    self.buy_vt_orderids = self.buy(self.boll_up, self.fixed_size, True)
            else:
                for vt_orderid in self.buy_vt_orderids:
                    self.cancel_order(vt_orderid)
                   
            if not self.short_vt_orderids:
                if self.cci < 0:
                    self.short_vt_orderids = self.short(self.boll_down, self.fixed_size, True)
            else:
                for vt_orderid in self.short_vt_orderids:
                    self.cancel_order(vt_orderid)

        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if self.cci < 0:
                    self.sell_vt_orderids = self.sell(self.boll_down, abs(self.pos), True)
            else:
                for vt_orderid in self.sell_vt_orderids:
                    self.cancel_order(vt_orderid)
        else:
            if not self.cover_vt_orderids:
                if self.cci > 0:
                    self.cover_vt_orderids = self.cover(self.boll_up, abs(self.pos), True)
            else:
                for vt_orderid in self.cover_vt_orderids:
                    self.cancel_order(vt_orderid)

        self.put_event()

    def on_Xmin2_bar(self, bar: BarData):
        """"""
        print(f"15minutebar.datetime:{bar.datetime}")
        am2 = self.am2
        am2.update_bar(bar)
        if not am2.inited:
            return

        self.cci = am2.cci(self.cci_window)
        
    def on_stop_order(self, stop_order: StopOrder):
        """"""
        if stop_order.status == StopOrderStatus.WAITING:
            return

        # 移除已经结束的停止单委托号
        for buf_orderids in [
            self.buy_vt_orderids,
            self.sell_vt_orderids,
            self.short_vt_orderids,
            self.cover_vt_orderids
        ]:
            if stop_order.stop_orderid in buf_orderids:
                buf_orderids.remove(stop_order.stop_orderid)
       
    def on_trade(self, trade: TradeData):
        """"""
       
    def on_order(self, order):
        """"""


class NewArrayManager(ArrayManager):
    """"""
    def __init__(self, size=100):
        """"""
        super().__init__(size)

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
    vt_symbol="rb888.SHFE",
    interval="1m",
    start=datetime(2020, 1, 1),
    end=datetime(2020,12,31),
    rate=0.0001,
    slippage=1,
    size=10,
    pricetick=1,
    capital=50000,
    mode=BacktestingMode.BAR
)
engine.add_strategy(CCIBollStrategy, {})
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
# setting.add_parameter("bar_window_length1", 1, 30, 1)
# setting.add_parameter("bar_window_length2", 15, 45, 1)
# setting.add_parameter("cci_window", 3, 33, 1)
# setting.add_parameter("boll_window", 10, 30, 1)
# # setting.add_parameter("cover_multiplier", 1.01, 1.20, 0.01)
# setting.add_parameter("pricetick_multiplier", 1, 5, 1)
#%%
# engine.run_optimization(setting, output=True)
# %%
