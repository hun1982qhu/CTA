#%%

from typing import Any
from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager,
    TradeData
)
from vnpy.trader.object import (BarData, TickData)
from vnpy.trader.constant import Interval


#%%
class CCIStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"

    cci_window = 8
    minute_window = 5
    fixed_size = 1
    sell_multiplier = 0.95
    cover_multiplier = 1.01
    pricetick_multilplier = 1

    cci = 0.0
    intra_trade_high = 0.0
    intra_trade_low = 0.0
    long_entry = 0.0
    short_entry = 0.0
    over_sold = None
    over_bought = None

    parameters = [
        "cci_window",
        "minute_window",
        "fixed_size",
        "sell_multiplier",
        "cover_multiplier",
        "pricetick_multilplier"
    ]
    variables = [
        "cci",
        "intra_trade_high",
        "intra_trade_low",
        "long_entry",
        "short_entry",
        "over_sold",
        "over_bought"
    ]

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar, self.minute_window, self.on_5min_bar, Interval.MINUTE)
        self.am = ArrayManager()

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
        """"""
        self.bg.update_bar(bar)

    def on_5min_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        self.cci = am.cci(self.cci_window)

        self.over_sold = (self.cci <= -100)
        self.over_bought = (self.cci >= 100)

        pricetick = self.get_pricetick()

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if self.over_sold:
                self.short(bar.close_price - pricetick * self.pricetick_multilplier, self.fixed_size, True)

            if self.over_bought:
                self.buy(bar.close_price + pricetick * self.pricetick_multilplier, self.fixed_size, True)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            self.short_entry = self.intra_trade_high * self.sell_multiplier

            self.sell(self.short_entry, abs(self.pos), True)

        else:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            self.long_entry = self.intra_trade_low * self.cover_multiplier

            self.cover(self.long_entry, abs(self.pos), True)

        print(bar.datetime)

        self.put_event()

    def on_trade(self, trade: TradeData):
        """"""
        print(trade.orderid, trade.datetime)
        self.put_event()