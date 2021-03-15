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
#%%
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.base import BacktestingMode
from datetime import datetime
#%%
class CCIStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"

    cci_window = 6
    minute_window = 2
    fixed_size = 1
    sell_multiplier = 0.91
    cover_multiplier = 1.06
    pricetick_multilplier = 1
    
    long_entry = 0.0
    short_entry = 0.0
    cci = 0.0

    cci_intra_trade = 0.0
    cci_intra_trade_high = 0.0
    cci_intra_trade_low = 0.0

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
        "cci_intra_trade",
        "cci_intra_trade_high",
        "cci_intra_trade_low"
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
        
        self.buy_orderids = []
        self.sell_orderids = []
        self.short_orderids = []
        self.cover_orderids = []

        self.pricetick = self.get_pricetick()

        # 新增，状态控制初始化
        self.chase_long_trigger = False
        self.chase_sell_trigger = False
        self.chase_short_trigger = False
        self.chase_cover_trigger = False
        self.long_trade_volume = 0
        self.short_trade_volume = 0
        self.sell_trade_volume = 0
        self.cover_trade_volume = 0
        self.chase_interval = 10  # 拆单间隔：秒

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

        # 调用cta策略模板新增的get_position_detail函数，通过engine获得活动委托字典active_orders
        # 需要注意的是：active_orders只缓存未成交或者部分成交的委托，其中key是字符串格式的vt_orderid，value对应OrderData对象
        active_orders = self.get_position_detail(tick.vt_symbol).active_orders

        if active_orders:
            # 委托完成状态
            order_finished = False
            vt_orderid = list(active_orders.keys())[0]  # 委托单vt_orderid
            order = list(active_orders.values())[0]  # 委托单字典

            # 开仓追单，部分交易没有开平仓指令（Offset.NONE） Offset代表仓位的开平
            if order.offset in (Offset.NONE, Offset.OPEN):
                if order.direction == Direction.LONG:
                    self.long_trade_volume = order.untraded
                    if (tick.datetime - order.datetime).seconds > self.chase_interval and self.long_trade_volume > 0 and (not self.chase_long_trigger) and vt_orderid:
                        # 撤销之前发出的未成交订单
                        self.cancel_order(vt_orderid)
                        self.chase_long_trigger = True
                elif order.direction == Direction.SHORT:
                    self.short_trade_volume = order.untraded
                    if (tick.datetime - order.datetime).seconds > self.chase_interval and self.short_trade_volume > 0 and (not self.chase_short_trigger) and vt_orderid:
                        self.cancel_order(vt_orderid)
                        self.chase_short_trigger = True
            # 平仓追单
            elif order.offset in (Offset.CLOSE, Offset.CLOSETODAY):
                if order.direction == Direction.SHORT:
                    self.short_trade_volume = order.untraded
                    if (tick.datetime - order.datetime).seconds > self.chase_interval and self.sell_trade_volume > 0 and (not self.chase_sell_trigger) and vt_orderid:
                        self.cancel_order(vt_orderid)
                        self.chase_sell_trigger = True
                if order.direction == Direction.LONG:
                    self.cover_trade_volume = order.untraded
                    if (tick.datetime - order.datetime).seconds > self.chase_interval and self.cover_trade_volume > 0 and (not self.chase_cover_trigger) and vt_orderid:
                        self.cancel_order(vt_orderid)
                        self.chase_cover_trigger = True
        # engine取到的活动委托为空，表示委托已完成
        else:
            order_finished = True
        if self.chase_long_trigger and order_finished:
            self.buy(tick.ask_price_1, self.long_trade_volume)
            self.chase_long_trigger = False
        elif self.chase_short_trigger and order_finished:
            self.short(tick.bid_price_1, self.short_trade_volume)
            self.chase_long_trigger = False
        elif self.chase_sell_trigger and order_finished:
            self.sell(tick.bid_price_1, self.sell_trade_volume)
            self.chase_sell_trigger = False
        elif self.chase_cover_trigger and order_finished:
            self.cover(tick.ask_price_1, self.cover_trade_volume)
            self.chase_cover_trigger = False         

    def on_bar(self, bar: BarData):
        """"""
        self.bg.update_bar(bar)

    def on_xmin_bar(self, bar: BarData):
        """"""
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        cci = am.cci(self.cci_window, True)
        self.cci = cci[-1]

        if self.pos == 0:
            self.cci_intra_trade = self.cci
            if self.cci <= -100:
                self.long_entry = bar.close_price + self.pricetick * self.pricetick_multilplier
                self.buy(self.long_entry, self.fixed_size)
            elif self.cci >= 100:
                self.short_entry = bar.close_price - self.pricetick * self.pricetick_multilplier
                self.short(self.short_entry, self.fixed_size)
        elif self.pos > 0:
            self.cci_intra_trade_high = max(self.cci_intra_trade, self.cci)
            self.short_entry = bar.close_price - self.pricetick * self.pricetick_multilplier
            if self.cci < self.cci_intra_trade_high * self.sell_multiplier:
                self.sell(self.short_entry, self.fixed_size)
        else:
            self.cci_intra_trade_low = min(self.cci_intra_trade, self.cci)
            self.long_entry = bar.close_price + self.pricetick * self.pricetick_multilplier
            if self.cci > self.cci_intra_trade_low * self.cover_multiplier:
                self.cover(self.long_entry, self.fixed_size)

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """        
        
    def cancel_orders(self, vt_orders: list):
        for vt_orderid in vt_orders:
            self.cancel_order(vt_orderid)
#%%
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

    def update_tick(self, tick: TickData) -> None:
        """
        Update new tick data into generator.
        """
        new_minute = False

        # Filter tick data with 0 last price
        if not tick.last_price:
            return

        # Filter tick data with less intraday trading volume (i.e. older timestamp)
        if self.last_tick and tick.volume and tick.volume < self.last_tick.volume:
            return

        if not self.bar:
            new_minute = True
        elif(self.bar.datetime.minute != tick.datetime.minute) or (self.bar.datetime.hour != tick.datetime.hour):
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

        self.last_tick = tick

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
#%%
engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="rb888.SHFE",
    interval="1m",
    start=datetime(2020, 1, 2),
    end=datetime(2020,1, 3),
    rate=0.000,
    slippage=0.2,
    size=1,
    pricetick=0.2,
    capital=1_000_000,
    mode=BacktestingMode.TICK
)
engine.add_strategy(CCIStrategy, {})
# %%
engine.load_data()
engine.run_backtesting()
# %%
