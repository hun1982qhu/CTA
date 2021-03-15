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

    bar_window_length = 1
    cci_window = 4
    fixed_size = 10
    pricetick_multilplier1 = 8
    pricetick_multilplier2 = 0
    kdj_overbought_line = 80
    kdj_oversold_line = 20
    fastk_period = 9
    slowk_period = 5
    slowk_matype = 0
    slowd_period = 5
    slowd_matype = 0

    k1 = 0
    k2 = 0
    d1 = 0
    d2 = 0

    cci1 = 0
    cci2 = 0

    parameters = [
        "bar_window_length",
        "fixed_size",
        "pricetick_multilplier1",
        "pricetick_multilplier2",
        "kdj_overbought_line",
        "kdj_oversold_line",
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
        "d2",
        "cci1",
        "cci2"
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

        self.pricetick = self.get_pricetick()

        self.buy_vt_orderids = []
        self.sell_vt_orderids = []
        self.short_vt_orderids = []
        self.cover_vt_orderids = []

        self.buy_price = 0
        self.sell_price = 0
        self.short_price = 0
        self.cover_price = 0

        self.kdj_cross_over = False
        self.kdj_cross_below = False

        self.cci_cross_over_100 = False
        self.cci_cross_below_100 = False
        self.cci_cross_over_min100 = False
        self.cci_cross_below_min100 = False

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
        cci = self.am.cci(self.cci_window, True)

        self.cci1 = cci[-1]
        self.cci2 = cci[-2]

        self.cci_cross_over_100 = (self.cci2 <= 100 and self.cci1 >= 100)
        self.cci_cross_below_100 = (self.cci2 >= 100 and self.cci1 <= 100)
        self.cci_cross_over_min100 = (self.cci2 <= -100 and self.cci1 >= -100)
        self.cci_cross_below_min100 = (self.cci2 >= -100 and self.cci1 <= -100)

        active_stop_orders = self.cta_engine.active_stop_orders
        if active_stop_orders:    
            stop_orderid = list(active_stop_orders.keys())[0]
            stop_order = list(active_stop_orders.values())[0]

            if stop_order.direction == Direction.LONG and stop_order.offset == Offset.OPEN:
                self.cancel_order(stop_orderid)
                self.buy(bar.close_price + self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)
            
            elif stop_order.direction == Direction.SHORT and stop_order.offset == Offset.OPEN:
                self.cancel_order(stop_orderid)
                self.short(bar.close_price - self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)
            
            elif stop_order.direction == Direction.LONG and stop_order.offset == Offset.CLOSE:
                self.cancel_order(stop_orderid)
                self.sell(bar.close_price - self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)

            elif stop_order.direction == Direction.SHORT and stop_order.offset == Offset.CLOSE:
                self.cancel_order(stop_orderid)
                self.cover(bar.close_price + self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)

    def on_Xmin_bar(self, bar: BarData):
        """"""
        am = self.am

        am.update_bar(bar)
        if not am.inited:
            return
        
        self.slowk, self.slowd, self.slowj = am.kdj(
            self.fastk_period,
            self.slowk_period,
            self.slowk_matype,
            self.slowd_period,
            self.slowd_matype,
            array=True
            )
        
        self.k1 = self.slowk[-1]
        self.k2 = self.slowk[-2]
        self.d1 = self.slowd[-1]
        self.d2 = self.slowd[-2]

        self.kdj_cross_over = (self.k2 < self.d2 and self.k1 > self.d1)
        self.kdj_cross_below = (self.k2 > self.d2 and self.k1 < self.d1)
        
        if self.pos == 0:            
            self.buy_price = bar.close_price + self.pricetick * self.pricetick_multilplier1
            self.sell_price = 0
            self.short_price = bar.close_price - self.pricetick * self.pricetick_multilplier1
            self.cover_price = 0

        elif self.pos > 0:            
            self.buy_price = 0
            self.sell_price = bar.close_price - self.pricetick * self.pricetick_multilplier1
            self.short_price = 0
            self.cover_price = 0

        else:
            self.buy_price = 0
            self.sell_price = 0
            self.short_price = 0
            self.cover_price = bar.close_price + self.pricetick * self.pricetick_multilplier1

        if self.pos == 0:
            if not self.buy_vt_orderids:
                if self.d1 > self.kdj_overbought_line and self.kdj_cross_over and (self.cci_cross_over_100 or self.cci_cross_over_min100):
                    self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
                    self.buy_price = 0               
            else:
                for vt_orderid in self.buy_vt_orderids:
                    self.cancel_order(vt_orderid)
                   
            if not self.short_vt_orderids:
                if self.d1 < self.kdj_oversold_line and self.kdj_cross_below and (self.cci_cross_below_100 or self.cci_cross_below_min100):
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    self.short_price = 0       
            else:
                for vt_orderid in self.short_vt_orderids:
                    self.cancel_order(vt_orderid)

        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if self.d1 > self.kdj_overbought_line and self.kdj_cross_below and (self.cci_cross_below_100 or self.cci_cross_below_min100):
                    self.sell_vt_orderids = self.sell(self.sell_price, abs(self.pos), True)
                    self.sell_price = 0      
            else:
                for vt_orderid in self.sell_vt_orderids:
                    self.cancel_order(vt_orderid)
                    
        else:
            if not self.cover_vt_orderids:
                if self.d1 < self.kdj_oversold_line and self.kdj_cross_over and (self.cci_cross_over_100 or self.cci_cross_over_min100):
                    self.cover_vt_orderids = self.cover(self.cover_price, abs(self.pos), True)
                    self.cover_price = 0                    
            else:
                for vt_orderid in self.cover_vt_orderids:
                    self.cancel_order(vt_orderid)

        self.put_event()
                
    def on_stop_order(self, stop_order: StopOrder):
        """"""
        # 只处理撤销（CANCELLED）或者触发（TRIGGERED）的停止委托单 
        if stop_order.status == StopOrderStatus.WAITING:
            print(f"还在waiting状态的stop_order:{stop_order.stop_orderid}")
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
        """
        Callback of new trade data update.
        """
        # 发出新的委托
        if self.pos == 0:
            if not self.buy_vt_orderids:
                if self.d1 > self.kdj_overbought_line and self.kdj_cross_over and (self.cci_cross_over_100 or self.cci_cross_over_min100):
                    self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
                    self.buy_price = 0
                    
            if not self.short_vt_orderids:
                if self.d1 < self.kdj_oversold_line and self.kdj_cross_below and (self.cci_cross_below_100 or self.cci_cross_below_min100):
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    self.short_price = 0
                    
        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if self.d1 > self.kdj_overbought_line and self.kdj_cross_below and (self.cci_cross_below_100 or self.cci_cross_below_min100):
                    self.sell_vt_orderids = self.sell(self.sell_price, abs(self.pos), True)
                    self.sell_price = 0
                    
        else:
            if not self.cover_vt_orderids:
                if self.d1 < self.kdj_oversold_line and self.kdj_cross_over and (self.cci_cross_over_100 or self.cci_cross_over_min100):
                    self.cover_vt_orderids = self.cover(self.cover_price, abs(self.pos), True)
                    self.cover_price = 0

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
    start=datetime(2017, 10, 15),
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
# %%
