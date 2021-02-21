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
from vnpy.trader.constant import Interval, Offset, Direction, Exchange
import numpy as np
import pandas as pd
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

        self.pricetick = self.get_pricetick()

        self.buy_vt_orderids = []
        self.sell_vt_orderids = []
        self.short_vt_orderids = []
        self.cover_vt_orderids = []

        self.buy_price = 0
        self.sell_price = 0
        self.short_price = 0
        self.cover_price = 0

        self.cross_over = None
        self.cross_below = None

        self.vt_count: int = 0

        self.long_untraded = 0
        self.long_diff = 0
        self.long_diff_list = []

        self.short_untraded = 0
        self.short_diff = 0
        self.short_diff_list = []

        self.long_stop_orders = []
        self.short_stop_orders = []

        # self.slowk = []
        # self.slowd = []
        # self.slowj = []

        # self.original = pd.DataFrame()
        
        # self.bo = []
        # self.bc = []
        # self.bh = []
        # self.bl = []
        # self.bt = []

        # self.sd_rec = pd.DataFrame()
        # self.sd_vtid = []
        # self.sd_id = []
        # self.sd_time = []
        # self.sd_price = []
        
        # self.td_rec = pd.DataFrame()
        # self.td_id = []
        # self.td_time = []
        # self.td_price = []        
        # self.td_vtid = []
        # self.td_orderid = []

        self.stoporder_count1 = 0
        self.stoporder_count2 = 0
        self.stoporder_count3 = 0
        self.stoporder_count4 = 0
        self.stoporder_count5 = 0
        self.stoporder_count6 = 0
        self.stoporder_count7 = 0
        self.stoporder_count8 = 0

        self.cancel_count1 = 0
        self.cancel_count2 = 0
        self.cancel_count3 = 0
        self.cancel_count4 = 0

        self.sell_orderid: str = ""

        self.sell_count = 0

        self.waiting_count = 0
        self.cancelled_count = 0
        self.triggered_count = 0

        self.bar = None

        self.timelist = []

        self.list = []

        self.bar_test = False
        self.bar_count = 0

        self.stop_order_removelist = []  

    def on_init(self):
        """"""
        self.write_log("策略初始化")
        self.load_bar(1)

    def on_start(self):
        """"""
        self.write_log("策略启动")

    def on_stop(self):
        """"""
        # self.original["k"] = self.k[-300:]
        # self.original["d"] = self.d[-300:]
        # self.original["j"] = self.j[-300:]
        # self.original["bo"] = self.bo
        # self.original["bc"] = self.bc
        # self.original["bh"] = self.bh
        # self.original["bl"] = self.bl
        # self.original.index = self.bt

        # self.sd_rec.index = self.sd_id
        # self.sd_rec["sd_price"] = self.sd_price
        # print(self.sd_rec)

        # plt.figure(figsize=(20, 8))
        # plt.plot(self.original["k"], color="r")
        # plt.plot(self.original["d"], color="b")
        # plt.plot(self.original["j"], color="y")
        # plt.plot(self.original["bo"], color="r")
        # plt.plot(self.original["bc"], color="b")
        # plt.plot(self.original["bh"], color="y")
        # plt.plot(self.original["bl"], color="g")
        # plt.plot(self.sd_rec["sd_price"], color="r")
        # plt.legend()
        # plt.show()

        # print(self.original[["bo", "bc", "bh", "bl"]].tail())
        # print(self.original.index)
        # print(self.original.iloc[[0, 1, 3]])
        # print(self.original.loc[:, ["bo"]])
        # print(self.original.iloc[:, [1, 2]])
        # print(self.original.loc["2019-10-16 14:12:00+08:00", "bo"])
        # print(self.original.iloc[42, 0])
        # print(self.original.iloc[[0, 2, 80], [0, 1]])
        self.write_log("策略停止")
        # print(self.long_diff_list)
        # print(self.short_diff_list)
        print(f"long_stop_orders\t长度{len(self.long_stop_orders)}")
        print(f"short_stop_orders\t长度{len(self.short_stop_orders)}")
        print(f"STOP.349出现的次数为:{self.short_stop_orders.count('STOP.349')}")
        myset = set(self.short_stop_orders)
        print(len(myset))
        errorlist = []
        for item in myset:
            # print(f"{item}出现了{self.short_stop_orders.count(item)}次")
            if self.short_stop_orders.count(item) > 3:
                errorlist.append(str(item))
        print(f"errorlist:{errorlist}")
        for i in errorlist:
            if i in self.stop_order_removelist:
                print(i)

        # print(f"timelist:{self.timelist}") 
        # print(f"self.list的长度{len(self.list)}")
        # print(f"timelist的长度{len(self.timelist)}")               
        print(f"在on_xmin_bar下的buy_stop_order:              {self.stoporder_count1}")
        print(f"在on_xmin_bar下取消buy_stop_order的次数:       {self.cancel_count1}\n")
        print(f"在on_xmin_bar下的short_stop_order:            {self.stoporder_count2}")
        print(f"在on_xmin_bar下取消short_stop_order的次数:     {self.cancel_count2}\n")
        print(f"在on_xmin_bar下的sell_stop_order:             {self.stoporder_count3}")
        print(f"在on_xmin_bar下取消sell_stop_order的次数:      {self.cancel_count3}\n")
        print(f"在on_xmin_bar下的cover_stop_order:            {self.stoporder_count4}")
        print(f"在on_xmin_bar下取消cover_stop_order的次数:     {self.cancel_count4}\n")
        print(f"在on_stop_order下的buy_stop_order:            {self.stoporder_count5}")
        print(f"在on_stop_order下的short_stop_order:          {self.stoporder_count6}")
        print(f"在on_stop_order下的sell_stop_order:           {self.stoporder_count7}")
        print(f"在on_stop_order下的cover_stop_order:          {self.stoporder_count8}")
        
        
        
        # print(f"self.sell_count:{self.sell_count}")
        print(f"self.waiting_count:{self.waiting_count}")
        print(f"self.cancelled_count:{self.cancelled_count}")
        print(f"self.triggered_count:{self.triggered_count}")
        # print(f"self.cta_engine.stop_orders:{self.cta_engine.stop_orders}\n\n长度为{len(self.cta_engine.stop_orders)}")
        print("策略停止")
        # print(f"看多委托未成交次数为{self.long_untraded}")
        # print(f"stop_order.price - long_cross_price平均值：{np.mean(self.long_diff_list)}")
        # print(f"看空委托未成交次数为{self.short_untraded}")
        # print(f"short_cross_price - stop_order.price：{np.mean(self.short_diff_list)}")
        
    def on_tick(self, tick: TickData):
        """"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.bg.update_bar(bar)
        
    def on_Xmin_bar(self, bar: BarData):
        """"""        
        # for stop_order in list(self.cta_engine.active_stop_orders.values()):
        #     print(f"stop_order展示:{stop_order}")

        # if self.bar == None:
        #     self.bar = bar

        # timedelta = bar.datetime.minute - self.bar.datetime.minute

        # if timedelta > 3:
        #     self.timelist.append(self.bar.datetime.strftime("%Y-%m-%d %H:%M:%S"))
        #     self.timelist.append(bar.datetime.strftime("%Y-%m-%d %H:%M:%S"))

        am = self.am

        am.update_bar(bar)
        if not am.inited:
            self.write_log(f"当前bar数量为：{str(self.am.count)}, 还差{str(self.am.size - self.am.count)}条")
            return
        
        self.slowk, self.slowd, self.slowj = am.kdj(
            self.fastk_period,
            self.slowk_period,
            self.slowk_matype,
            self.slowd_period,
            self.slowd_matype,
            array=True
            )

        # self.slowk, self.slowd, self.slowj = am.kdjs(
        #     9,
        #     array=True
        #     )

        # self.k.append(self.slowk[-1])
        # self.d.append(self.slowd[-1])
        # self.j.append(self.slowj[-1])
        
        self.k1 = self.slowk[-1]
        self.k2 = self.slowk[-2]
        self.d1 = self.slowd[-1]
        self.d2 = self.slowd[-2]

        self.cross_over = (self.k2 < self.d2 and self.k1 > self.d1)
        self.cross_below = (self.k2 > self.d2 and self.k1 < self.d1)
        
        if self.pos == 0:            
            self.buy_price = bar.close_price + self.pricetick * self.pricetick_multilplier
            self.sell_price = 0
            self.short_price = bar.close_price - self.pricetick * self.pricetick_multilplier
            self.cover_price = 0

        elif self.pos > 0:            
            self.buy_price = 0
            self.sell_price = bar.close_price - self.pricetick * self.pricetick_multilplier
            self.short_price = 0
            self.cover_price = 0

        else:
            self.buy_price = 0
            self.sell_price = 0
            self.short_price = 0
            self.cover_price = bar.close_price + self.pricetick * self.pricetick_multilplier
        
        
        if self.pos == 0:
            if not self.buy_vt_orderids:
                if self.d1 > 80 and self.cross_over:
                    self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
                    if 'STOP.349' in self.buy_vt_orderids:
                        print("在1这")
                    self.stoporder_count1 += 1
                    self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t开多仓委托：{self.buy_vt_orderids}")
                    self.buy_price = 0               
            else:
                for vt_orderid in self.buy_vt_orderids:
                    self.cancel_order(vt_orderid)
                    self.cancel_count1 += 1
                   

            if not self.short_vt_orderids:
                if self.d1 < 20 and self.cross_below:
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    if 'STOP.349' in self.short_vt_orderids:
                        print("在2这")
                    self.stoporder_count2 += 1
                    self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t开空仓委托：{self.short_vt_orderids}")
                    self.short_price = 0       
            else:
                for vt_orderid in self.short_vt_orderids:
                    if vt_orderid == "STOP.349":
                        print(vt_orderid)
                        print("349号停止单此时被取消了")
                        print(f"此时的self.pos为:{self.pos}")
                    self.cancel_order(vt_orderid)
                    self.cancel_count2 += 1

        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if self.d1 > 80 and self.cross_below:
                    self.sell_vt_orderids = self.sell(self.sell_price, abs(self.pos), True)
                    if 'STOP.349' in self.sell_vt_orderids:
                        print("在3这")
                    self.stoporder_count3 += 1
                    self.sell_orderid = self.sell_vt_orderids[0]
                    self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t平多仓委托：{self.sell_vt_orderids}")
                    self.sell_price = 0      
            else:
                for vt_orderid in self.sell_vt_orderids:
                    self.cancel_order(vt_orderid)
                    self.cancel_count3 += 1
                    
        else:
            if not self.cover_vt_orderids:
                if self.d1 < 20 and self.cross_over:
                    self.cover_vt_orderids = self.cover(self.cover_price, abs(self.pos), True)
                    if 'STOP.349' in self.cover_vt_orderids:
                        print("在4这")
                    self.stoporder_count4 += 1
                    self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t平空仓委托：{self.cover_vt_orderids}")
                    self.cover_price = 0                    
            else:
                for vt_orderid in self.cover_vt_orderids:
                    self.cancel_order(vt_orderid)
                    self.cancel_count4 += 1

        self.put_event()
                
    def on_stop_order(self, stop_order: StopOrder):
        """"""

        # self.sd_id.append(stop_order.stop_orderid)
        # self.sd_price.append(stop_order.price)

        # 只处理撤销（CANCELLED）或者触发（TRIGGERED）的停止委托单
        if stop_order.status == StopOrderStatus.WAITING:
            self.waiting_count += 1
        if stop_order.status == StopOrderStatus.CANCELLED:
            self.cancelled_count += 1
        if stop_order.status == StopOrderStatus.TRIGGERED:
            print(f"triggered:{stop_order.offset}{stop_order.direction}")
            self.triggered_count += 1

        if stop_order.status == StopOrderStatus.WAITING: # or stop_order.status == StopOrderStatus.TRIGGERED:
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
                self.stop_order_removelist.append(stop_order.stop_orderid)
                buf_orderids.remove(stop_order.stop_orderid)

        # 发出新的委托
        if self.pos == 0:
            if not self.buy_vt_orderids:
                if self.d1 > 80 and self.cross_over:
                    self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
                    if 'STOP.349' in self.buy_vt_orderids:
                        print("在5这")
                    self.stoporder_count5 += 1
                    self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t开多仓委托：{self.buy_vt_orderids}")
                    self.buy_price = 0
                    
            if not self.short_vt_orderids:
                if self.d1 < 20 and self.cross_below:
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    if 'STOP.349' in self.short_vt_orderids:
                        print("在6这")
                        print(f"此时的self.pos为:{self.pos}")
                        print(f"STOP.349为:{self.cta_engine.active_stop_orders['STOP.349']}")
                    self.stoporder_count6 += 1
                    self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t开空仓委托：{self.short_vt_orderids}")
                    self.short_price = 0
                    
        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if self.d1 > 80 and self.cross_below:
                    self.sell_vt_orderids = self.sell(self.sell_price, abs(self.pos), True)
                    if 'STOP.349' in self.sell_vt_orderids:
                        print("在7这")
                    self.stoporder_count7 += 1
                    self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t平多仓委托：{self.sell_vt_orderids}")
                    self.sell_price = 0
                    
        else:
            if not self.cover_vt_orderids:
                if self.d1 < 20 and self.cross_over:
                    self.cover_vt_orderids = self.cover(self.cover_price, abs(self.pos), True)
                    if "STOP.349" in self.cover_vt_orderids:
                        print("在8这")
                    self.stoporder_count8 += 1
                    self.vt_count += 1
                    # print(f"第{self.vt_count}次委托\t委托时间：{self.cta_engine.datetime}\t平空仓委托：{self.cover_vt_orderids}")
                    self.cover_price = 0
                    
    # def on_trade(self, trade: TradeData):
    #     print(trade.direction)
    #     print(trade.offset)

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        # print(trade.vt_orderid)
        # print(trade.vt_tradeid)
        # if trade.direction == "平" and trade.orderid == self.sell_orderid:
        #     self.sell_count += 1
        

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
start = time.time()
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
engine.load_data()
#%%
engine.run_backtesting()
#%%
engine.calculate_result()
engine.calculate_statistics()
# 待测试的代码
end = time.time()
print(f"Running time: {(end-start)} Seconds")
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
# result1 = engine.run_optimization(setting, output=True)
# print(result1[1])
#%%
# print(result1[2])
#%%
# print(result1[15])

# %%
