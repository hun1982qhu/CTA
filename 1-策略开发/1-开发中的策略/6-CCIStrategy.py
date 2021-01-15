#%%

from typing import Any, Callable
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

    atr_window = 25
    cci_window = 6
    minute_window = 32
    fixed_size = 1
    sell_multiplier = 0.91
    cover_multiplier = 1.06
    pricetick_multilplier = 1

    atr_value = 0.0
    atr_ma = 0.0
    long_entry = 0.0
    short_entry = 0.0
    cci1 = 0.0
    cci2 = 0.0
    cci3 = 0.0

    parameters = [
        "atr_window",
        "cci_window",
        "minute_window",
        "fixed_size",
        "sell_multiplier",
        "cover_multiplier",
        "pricetick_multilplier"
    ]
    variables = [
        "atr_value",
        "atr_ma",
        "long_entry",
        "short_entry",
        "cci1",
        "cci2",
        "cci3"
    ]

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = XminBarGenerator(self.on_bar, self.minute_window, self.on_xmin_bar, Interval.MINUTE)
        self.am = ArrayManager()

        self.over_sold = None
        self.low_turning_cond1 = None
        self.low_turning_cond2 = None
        self.over_bought = None
        self.high_turning_cond1 = None
        self.high_turning_cond2 = None

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
        """"""
        self.bg.update_bar(bar)

    def on_xmin_bar(self, bar: BarData):
        """"""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        atr_array = am.atr(self.atr_window, True)
        self.atr_value = atr_array[-1]
        self.atr_ma = atr_array[-self.atr_window:].mean()
        
        cci = am.cci(self.cci_window, True)
        self.cci1 = cci[-1]
        self.cci2 = cci[-2]
        self.cci3 = cci[-3]

        self.over_sold = (self.cci1 <= -100)
        self.over_bought = (self.cci1 >= 100)

        self.low_turning_cond1 = (self.cci1 > self.cci2)
        self.low_turning_cond2 = (self.cci3 > self.cci2)
        
        self.high_turning_cond1 = (self.cci1 < self.cci2)
        self.high_turning_cond2 = (self.cci3 < self.cci2)

        self.short_entry = bar.close_price - self.pricetick * self.pricetick_multilplier
        self.long_entry = bar.close_price + self.pricetick * self.pricetick_multilplier

        if self.atr_value > self.atr_ma:
            if self.pos == 0:
                if self.over_sold:
                    self.buy(self.long_entry, self.fixed_size, True)

                if self.over_bought:
                    self.short(self.short_entry, self.fixed_size, True)

        elif self.pos > 0:
            if self.high_turning_cond1 & self.high_turning_cond2:
                self.sell(self.short_entry, abs(self.pos), True)

        else:
            if self.low_turning_cond1 & self.low_turning_cond2:
                self.cover(self.long_entry, abs(self.pos), True)

        self.put_event()


class XminBarGenerator(BarGenerator):
    """"""
    def __init__(
        self,
        on_bar: Callable,
        window: int = 0,
        on_window_bar: Callable = None,
        interval: Interval = Interval.MINUTE
    ):
        super().__init__(on_bar, window, on_window_bar, interval)

    def update_bar(self, bar: BarData) -> None:
        """
        Update 1 minute bar into generator
        """
        # If not inited, create window bar object
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
            # 以上3行代码为原来的代码，原来的代码只能合成能整除60的数字的分钟K线
            # 替换为以下4行代码后，可以合成任意分钟的K线，例如7分钟K线
            self.interval_count += 1

            if not self.interval_count % self.window:
                finished = True
                self.interval_count = 0
        elif self.interval == Interval.HOUR:
            if self.last_bar and bar.datetime.hour != self.last_bar.datetime.hour:
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


class XsecBarGenerator(BarGenerator):
    """"""
    def __init__(
        self,
        on_bar: Callable,
        window: int = 0,
        on_window_bar: Callable = None,
        interval: Interval = Interval.MINUTE
    ):
        super().__init__(on_bar, window, on_window_bar, interval)
    
    def update_tick(self, tick: TickData):
        """
        将实时tick数据更新到BarGenerator中
        """
        new_minute = False

        # Filter tick data with 0 last price
        if not tick.last_price:
            return

        # Filter tick data with older timestamp
        if self.last_tick and tick.datetime < self.last_tick.datetime:
            return

        if not self.bar:
            new_minute = True
        # elif self.bar.datetime.minute != tick.datetime.minute:
        # 通过以下逻辑合成50秒K线
        elif self.tick.datetime.second >= 50 and self.last_tick.datetime.second < 50:
            self.bar.datetime = self.bar.datetime.replace(
                second=0, microsecond=0
            )
            self.on_bar(self.bar)

            new_minute = True

        if new_minute:
            self.bar = BarData(
                symbol=tick.symbol,
                exchange=tick.exchange,
                interval=Interval.MINUTE,
                datetime=tick.datetime,
                gateway_name=tick.gateway_name,
                open_price=tick.last_price,
                high_price=tick.last_price,
                low_price=tick.last_price,
                close_price=tick.last_price,
                open_interest=tick.open_interest
            )
        else:
            self.bar.high_price = max(self.bar.high_price, tick.last_price)
            self.bar.low_price = min(self.bar.low_price, tick.last_price)
            self.bar.close_price = tick.last_price
            self.bar.open_interest = tick.open_interest
            self.bar.datetime = tick.datetime

        if self.last_tick:
            volume_change = tick.volume - self.last_tick.volume
            self.bar.volume += max(volume_change, 0)

        # 将最新的tick缓存到self.last_tick
        self.last_tick = tick