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

from vnpy.trader.ui import create_qapp, QtCore
from vnpy.chart import ChartWidget, VolumeItem, CandleItem

import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import style
mpl.rcParams['font.family'] = 'serif'  # 解决一些字体显示乱码的问题

style.use('ggplot')
import seaborn as sns

sns.set()

#%%
class CCIMACDStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"

    bar_window_length = 3
    fixed_size = 10
    cci_window = 3
    macd_fastk_period = 5
    macd_slowk_period = 12
    macd_dea_period = 5
    macd_drawback_pct = 0.90
    pricetick_multilplier1 = 1
    pricetick_multilplier2 = 0
    
    diff = 0 
    dea = 0 
    macd = 0

    parameters = [
        "bar_window_length",
        "fixed_size",
        "cci_window",
        "macd_fastk_period",
        "macd_slowk_period",
        "macd_dea_period",
        "macd_drawback_pct",
        "pricetick_multilplier1",
        "pricetick_multilplier2"
    ]

    variables = [
        "diff",
        "dea",
        "macd"
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

        self.cci_crossover_100 = False
        self.cci_crossbelow_100 = False
        self.cci_crossover_m100 = False
        self.cci_crossbelow_m100 = False

        self.macd_cross_over = False
        self.macd_cross_below = False

        self.intra_macd_high = 0
        self.intra_macd_low = 0

        self.macd_high_downtrend = False
        self.macd_low_uptrend = False

        self.chase_trigger = False

        self.count1 = 0
        self.count2 = 0
        self.count3 = 0
        self.count4 = 0

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
        # 
        # print(bar.datetime)
        # print(f"self.pos:{self.pos}")

        active_stop_orders = self.cta_engine.active_stop_orders

        if active_stop_orders and self.chase_trigger:    
            stop_orderid = list(active_stop_orders.keys())[0]
            stop_order = list(active_stop_orders.values())[0]
            
            if len(list(active_stop_orders.keys())) >= 2:
                print("list(active_stop_orders.keys())长度超过1")

            self.cancel_order(stop_orderid)

            if stop_order.direction == Direction.LONG and stop_order.offset == Offset.OPEN:
                self.buy(bar.close_price + self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)
            
            elif stop_order.direction == Direction.SHORT and stop_order.offset == Offset.OPEN:
                self.short(bar.close_price - self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)
            
            elif stop_order.direction == Direction.LONG and stop_order.offset == Offset.CLOSE:
                self.sell(bar.close_price - self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)

            elif stop_order.direction == Direction.SHORT and stop_order.offset == Offset.CLOSE:
                self.cover(bar.close_price + self.pricetick * self.pricetick_multilplier2, self.fixed_size, True)
            
            self.chase_trigger = False

    def on_Xmin_bar(self, bar: BarData):
        """"""
        am = self.am

        am.update_bar(bar)
        if not am.inited:
            return

        self.chase_trigger = True

        # 计算macd指标
        diff, dea, macd = am.macd(self.macd_fastk_period, self.macd_slowk_period, self.macd_dea_period, True)
        self.diff = diff[-1]
        self.dea = dea[-1]
        self.macd = macd[-1]

        # diff线由在dea线之下变为在dea线之上，表示市场行情由弱转强
        self.macd_cross_over = (macd[-2] < 0 and macd[-1] > 0)
        # diff线由在dea线之上变为在dea线之下，表示市场行情由强转弱
        self.macd_cross_below = (macd[-2] > 0 and macd[-1] < 0)

        # 计算cci指标
        cci = am.cci(self.cci_window, True)

        # cci线上穿100线，说明市场行情进入明显上升趋势，此时应顺势买入
        self.cci_crossover_100 = (cci[-2] < 100 and cci[-1] > 100)
        # cci线下穿100线，说明市场行情上升趋势已经结束，此时应顺势卖出
        self.cci_crossbelow_100 = (cci[-2] > 100 and cci[-1] < 100)
        # cci线上穿-100线，说明市场行情开始回调，应该顺势买入
        self.cci_crossover_m100 = (cci[-2] < -100 and cci[-1] > -100)
        # cci线下穿-100线，说明市场行情进入明显下跌趋势，应该顺势卖出
        self.cci_crossbelow_m100 = (cci[-2] > -100 and cci[-1] < -100)  

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
            # 用于缓存持仓期间最高或最低macd值
            self.intra_macd_high = self.macd
            self.intra_macd_low = self.macd

            if not self.buy_vt_orderids:
                if (self.cci_crossover_100 or self.cci_crossover_m100) and self.macd_cross_over:
                    self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
                    self.buy_price = 0      
            else:
                for vt_orderid in self.buy_vt_orderids:
                    self.cancel_order(vt_orderid)
                   
            if not self.short_vt_orderids:
                if (self.cci_crossbelow_100 or self.cci_crossbelow_m100) and self.macd_cross_below:
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    self.short_price = 0
            else:
                for vt_orderid in self.short_vt_orderids:
                    self.cancel_order(vt_orderid)

        elif self.pos > 0:
            # 缓存持多仓期间macd最大值
            self.intra_macd_high = max(self.intra_macd_high, self.macd)
            # 判断macd值低于持多仓期间macd最值的90%
            self.macd_high_downtrend = (self.macd <= self.intra_macd_high * self.macd_drawback_pct)

            if not self.sell_vt_orderids:
                # 当macd值低于最高值的90%，或者cci下穿100线，或者cci下穿-100线，就平多仓
                if self.macd_high_downtrend or self.cci_crossbelow_100 or self.cci_crossbelow_m100:
                    self.sell_vt_orderids = self.sell(self.short_price, self.fixed_size, True)
                    self.short_price = 0
            else:
                for vt_orderid in self.sell_vt_orderids:
                    self.cancel_order(vt_orderid)
                    
        else:
            # 缓存持空仓期间macd最小值
            self.intra_macd_low = min(self.intra_macd_low, self.macd)        
            # 判断macd值高于持空仓期间macd最值的90%
            self.macd_low_uptrend = (self.macd >= self.intra_macd_low * self.macd_drawback_pct)
            
            if not self.cover_vt_orderids:
                # 当macd值高于最低值的90%，或者cci上穿100线，或者cci上穿-100线，就平多仓
                if self.macd_low_uptrend or self.cci_crossover_100 or self.cci_crossover_m100:
                    self.cover_vt_orderids = self.cover(self.cover_price, self.fixed_size, True)
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

        # if stop_order.status == StopOrderStatus.CANCELLED:
        #     print(f"self.pos:{self.pos}")
        #     if self.pos == 0:
        #         if not self.buy_vt_orderids:
        #             if (self.cci_crossover_100 or self.cci_crossover_m100) and self.macd_cross_over:
        #                 self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
        #                 self.buy_price = 0
        #                 self.count1 += 1
        #                 print(f"buy:{self.count1}")    
                    
        #         if not self.short_vt_orderids:
        #             if (self.cci_crossbelow_100 or self.cci_crossbelow_m100) and self.macd_cross_below:
        #                 self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
        #                 self.short_price = 0
        #                 self.count2 += 1
        #                 print(f"short:{self.count2}")

        #     elif self.pos > 0:
        #         if not self.sell_vt_orderids:
        #             if self.macd_high_downtrend or self.cci_crossbelow_100 or self.cci_crossbelow_m100:
        #                 self.sell_vt_orderids = self.sell(self.short_price, self.fixed_size, True)
        #                 self.short_price = 0
        #                 self.count3 += 1
        #                 print(f"sell:{self.count3}")
                        
        #     else:
        #         if not self.cover_vt_orderids:
        #             if self.macd_low_uptrend or self.cci_crossover_100 or self.cci_crossover_m100:
        #                 self.cover_vt_orderids = self.cover(self.cover_price, self.fixed_size, True)
        #                 self.cover_price = 0
        #                 self.count4 += 1
        #                 print(f"cover:{self.count4}")

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        # print(f"self.pos:{self.pos}")
        # print(trade.orderid)


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
    end=datetime(2021, 4, 8),
    rate=0.0001,
    slippage=2.0,
    size=10,
    pricetick=1.0,
    capital=50000,
    mode=BacktestingMode.BAR
)
engine.add_strategy(CCIMACDStrategy, {})
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
# setting.add_parameter("bar_window_length", 1, 15, 1)
# setting.add_parameter("pricetick_multilplier1", 1, 10, 1)
# setting.add_parameter("macd_fastk_period", 4, 20, 2)
# setting.add_parameter("macd_slowk_period", 21, 30, 1)
# setting.add_parameter("macd_signal_period", 4, 12, 2)
#%%
# engine.run_optimization(setting, output=True)
# %%
