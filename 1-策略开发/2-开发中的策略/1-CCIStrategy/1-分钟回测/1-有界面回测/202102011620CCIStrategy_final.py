from typing import Any, Callable
from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager,
    TradeData,
    StopOrder,
    OrderData
)
from vnpy.app.cta_strategy.base import EngineType, StopOrderStatus
from vnpy.trader.object import (BarData, TickData)
from vnpy.trader.constant import Interval, Offset, Direction
import numpy as np
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.base import BacktestingMode
from datetime import datetime
import numpy as np
import pandas as pd
from vnpy.trader.constant import Status
import numpy as np


class CCIStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"

    bar_window_length = 3
    cci_window = 2
    fixed_size = 1
    sell_multiplier = 0.995
    cover_multiplier = 0.105
    pricetick_multilplier = 2
    
    cci1 = 0
    cci2 = 0
    cci_intra_trade = 0

    parameters = [
        "cci_window",
        "fixed_size",
        "sell_multiplier",
        "cover_multiplier",
        "pricetick_multilplier"
    ]

    variables = [
        "cci1",
        "cci2",
        "cci_intra_trade"
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
        self.am = ArrayManager()  

        self.pricetick = self.get_pricetick()
        
    def on_init(self):
        """"""
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """"""
        self.write_log("策略启动")

    def on_stop(self):
        """"""
        self.write_log("策略停止")
        
    def on_tick(self, tick: TickData):
        """"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.bg.update_bar(bar)
    
    def on_Xmin_bar(self, bar: BarData):
        """"""

        self.cancel_all()
        
        am = self.am

        am.update_bar(bar)
        if not am.inited:
            return

        cci = am.cci(self.cci_window, True)

        self.cci1 = cci[-1] + 1000
        self.cci2 = cci[-2] + 1000

        long_entry = bar.close_price + self.pricetick * self.pricetick_multilplier
        short_entry = bar.close_price - self.pricetick * self.pricetick_multilplier 

        if self.pos == 0:
            self.cci_intra_trade = self.cci1

            cross_over_100 = (self.cci2 < 1100 and self.cci1 > 1100)
            cross_below_100 = (self.cci2 > 1100 and self.cci1 < 1100)
            cross_over_min100 = (self.cci2 < 900 and self.cci1 > 900)
            cross_below_min100 = (self.cci2 > 900 and self.cci1 < 900)

            if cross_over_100 or cross_over_min100:
                self.buy(long_entry, self.fixed_size, True)
            elif cross_below_100 or cross_below_min100:
                self.short(short_entry, self.fixed_size, True)

        elif self.pos > 0:
            self.cci_intra_trade = max(self.cci_intra_trade, self.cci1)
            if self.cci1 < self.cci_intra_trade * self.sell_multiplier:
                self.sell(short_entry, abs(self.pos), True)
                # print("缓存最高CCI减去当前CCI值：", ((self.cci_intra_trade - self.cci1)/self.cci_intra_trade))

        else:
            self.cci_intra_trade = min(self.cci_intra_trade, self.cci1)
            if self.cci1 > self.cci_intra_trade * self.cover_multiplier:
                self.cover(long_entry, abs(self.pos), True)
                # print("当前CCI值减去缓存最高CCI：", ((self.cci1 - self.cci_intra_trade)/self.cci_intra_trade))

    # def on_stop_order(self, stop_order: StopOrder):
    #     print(stop_order.status)

    # def on_trade(self, trade: TradeData):
    #     print(trade.direction)
    #     print(trade.offset)

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