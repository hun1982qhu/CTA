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
from vnpy.app.cta_strategy.base import EngineType, StopOrderStatus
from vnpy.trader.object import (BarData, TickData)
from vnpy.trader.constant import Interval, Offset, Direction
import numpy as np
from vnpy.app.cta_strategy.backtesting1 import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.base import BacktestingMode
from datetime import datetime
import numpy as np
import pandas as pd
from vnpy.trader.ui import create_qapp, QtCore
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Exchange, Interval
from vnpy.chart import ChartWidget, VolumeItem, CandleItem
from vnpy.trader.constant import Status
#%%
class CCIStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"

    cci_window = 6
    minute_window = 2
    fixed_size = 1
    sell_multiplier = 0.91
    cover_multiplier = 1.06
    pricetick_multilplier = 25
    
    cci = 0.0

    cci_intra_trade = 0.0

    min_bar: BarData = None

    parameters = [
        "cci_window",
        "minute_window",
        "fixed_size",
        "sell_multiplier",
        "cover_multiplier",
        "pricetick_multilplier"
    ]

    variables = [
        "long_entry",
        "short_entry",
        "cci",
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
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()  

        self.pricetick = self.get_pricetick()

        # self.list1 = []
        # self.list2 = []
        self.list3 = []
        
    def on_init(self):
        """"""
        self.write_log("策略初始化")
        self.load_tick(10)

    def on_start(self):
        """"""
        self.write_log("策略启动")

    def on_stop(self):
        """"""
        print(len(self.list3))
        self.write_log("策略停止")
        
        # app = create_qapp()

        # bars = self.list2

        # widget = ChartWidget()
        # widget.add_plot("candle", hide_x_axis=True)
        # widget.add_plot("volume", maximum_height=200)
        # widget.add_item(CandleItem, "candle", "candle")
        # widget.add_item(VolumeItem, "volume", "volume")
        # widget.add_cursor()

        # n = 1000
        # history = bars[:n]
        # new_data = bars[n:]

        # widget.update_history(history)

        # def update_bar():
        #     bar = new_data.pop(0)
        #     widget.update_bar(bar)

        # timer = QtCore.QTimer()
        # timer.timeout.connect(update_bar)
        # # timer.start(100)

        # widget.show()
        # app.exec_()

    def on_tick(self, tick: TickData):
        """"""
        self.bg.update_tick(tick)
    
    def on_bar(self, bar: BarData):
        """"""
        # self.list2.append(bar)

        # self.cancel_all()
        
        engine.datetime = bar.datetime
        
        long_cross_price = bar.high_price
        short_cross_price = bar.low_price
        long_best_price = bar.open_price
        short_best_price = bar.open_price

        for stop_order in list(engine.active_stop_orders.values()):
            # Check whether stop order can be triggered.
            long_cross = (
                stop_order.direction == Direction.LONG
                and stop_order.price <= long_cross_price
            )

            short_cross = (
                stop_order.direction == Direction.SHORT
                and stop_order.price >= short_cross_price
            )

            # if stop_order.price <= long_cross_price:
            #     print("stop_order.price <= long_cross_price,", stop_order.price, long_cross_price)
            # elif stop_order.price >= short_cross_price:
            #     print("stop_order.price >= short_cross_price,", stop_order.price, long_cross_price)
            # else:
            #     print("不能成交")

            if not long_cross and not short_cross:
                continue

            # Create order data.
            engine.limit_order_count += 1

            order = OrderData(
                symbol=engine.symbol,
                exchange=engine.exchange,
                orderid=str(engine.limit_order_count),
                direction=stop_order.direction,
                offset=stop_order.offset,
                price=stop_order.price,
                volume=stop_order.volume,
                traded=stop_order.volume,
                status=Status.ALLTRADED,
                gateway_name=engine.gateway_name,
                datetime=engine.datetime
            )

            engine.limit_orders[order.vt_orderid] = order

            # Create trade data.
            if long_cross:
                trade_price = max(stop_order.price, long_best_price)
                pos_change = order.volume
            else:
                trade_price = min(stop_order.price, short_best_price)
                pos_change = -order.volume

            engine.trade_count += 1

            trade = TradeData(
                symbol=order.symbol,
                exchange=order.exchange,
                orderid=order.orderid,
                tradeid=str(engine.trade_count),
                direction=order.direction,
                offset=order.offset,
                price=trade_price,
                volume=order.volume,
                datetime=engine.datetime,
                gateway_name=engine.gateway_name,
            )

            engine.trades[trade.vt_tradeid] = trade

            # Update stop order.
            stop_order.vt_orderids.append(order.vt_orderid)
            stop_order.status = StopOrderStatus.TRIGGERED

            if stop_order.stop_orderid in engine.active_stop_orders:
                engine.active_stop_orders.pop(stop_order.stop_orderid)

            # Push update to strategy.
            self.on_stop_order(stop_order)
            self.on_order(order)

            engine.strategy.pos += pos_change
            self.on_trade(trade)

        am = self.am

        am.update_bar(bar)
        if not am.inited:
            return
            
        # engine.bar = bar
        # engine.datetime = bar.datetime
        # engine.cross_limit_order()
        # engine.cross_stop_order()        

        cci = am.cci(self.cci_window, True)

        self.cci = cci[-1]
        
        # self.cci_intra_trade = max(self.cci_intra_trade, self.cci)
        # down_ratio = (self.cci - self.cci_intra_trade)/self.cci_intra_trade

        # if self.cci < self.cci_intra_trade * self.sell_multiplier:
        #     print("cci:", self.cci)
        #     print("低于cci最高值9%：", down_ratio)

        if self.pos == 0:
            self.cci_intra_trade = self.cci
            long_entry = bar.high_price + self.pricetick * self.pricetick_multilplier
            short_entry = bar.low_price - self.pricetick * self.pricetick_multilplier
            if self.cci <= -100:                
                # print("pricetick：", self.pricetick)
                # print("bar.close_price：", bar.close_price)
                # print("pricetick_multiplier:", self.pricetick_multilplier)
                buy_order = self.buy(long_entry, self.fixed_size, True)
                # print("pos=0，cci值小于-100时开多，开仓价格：", long_entry)
                # print("buy_order:", buy_order)
                # for stop_order in list(engine.active_stop_orders.values()):
                #     print("stop_order.price:", stop_order.price) 
            elif self.cci >= 100:                
                # print("pricetick：", self.pricetick)
                # print("bar.close_price:", bar.close_price)
                # print("pricetick_multiplier:", self.pricetick_multilplier)
                short_order = self.short(short_entry, self.fixed_size, True)
                # print("pos=0，cci值大于100时开空，开仓价格：", short_entry)
                # print("short_order:", short_order)
                # for stop_order in list(engine.active_stop_orders.values()):
                #     print("stop_order.price:", stop_order.price) 
        elif self.pos > 0:
            self.cci_intra_trade = max(self.cci_intra_trade, self.cci)
            short_entry = bar.low_price - self.pricetick * self.pricetick_multilplier
            if self.cci < self.cci_intra_trade * self.sell_multiplier:
                self.sell(short_entry, abs(self.pos), True)
                # print("pos>0，cci最高值下降9%时平多，平多价格：", short_entry)
        else:
            self.cci_intra_trade = min(self.cci_intra_trade, self.cci)
            long_entry = bar.high_price + self.pricetick * self.pricetick_multilplier
            if self.cci > self.cci_intra_trade * self.cover_multiplier:
                self.cover(long_entry, abs(self.pos), True)
                # print("pos<0，cci最低值上升6%时平多，平空价格：", long_entry)
    
    def on_trade(self, trade):
        self.list3.append(trade)
        print("trade:", trade)

    def on_stop_order(self, stop_order):
        print("order:", stop_order)
  
#%%
engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="rb888.SHFE",
    interval="1m",
    start=datetime(2020, 4, 1),
    end=datetime(2020,7, 1),
    rate=0.000,
    slippage=0.2,
    size=1,
    pricetick=0.2,
    capital=1_000_000,
    mode=BacktestingMode.TICK
)
engine.add_strategy(CCIStrategy, {})
#%%
engine.load_data()
#%%
engine.run_backtesting()
#%%
engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()
# %%
