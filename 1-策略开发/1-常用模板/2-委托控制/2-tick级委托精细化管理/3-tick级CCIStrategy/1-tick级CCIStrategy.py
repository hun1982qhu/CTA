#%%
# 做一些小小改动
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
# CCI交易指标又叫顺势交易指标，是美国股市技术分析家唐纳德.蓝伯特（Donal Lambert）于20世纪80年代提出的，专门测量股价、外汇或者贵金属交易价格
# 是否已超出常态分布范围。CCI指标属于超买超卖类指标中较特殊的一种，波动于正无穷和负无穷大之间。但是，又不需要以0为中轴线
# 这一点也和波动于正无穷大和负无穷大的指标不同。
class CCIStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"

    atr_window = 25
    cci_window = 6
    minute_window = 2
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

        if self.atr_value > self.atr_ma:
            if self.pos == 0:
                if not self.buy_orderids:
                    self.long_entry = bar.close_price + self.pricetick * self.pricetick_multilplier
                    if self.over_sold:
                        self.buy_orderids = self.buy(self.long_entry, self.fixed_size, True)
                elif self.long_entry != (bar.close_price + self.pricetick * self.pricetick_multilplier):
                    self.cancel_orders(self.buy_orderids)

                if not self.short_orderids:
                    self.short_entry = bar.close_price - self.pricetick * self.pricetick_multilplier
                    if self.over_bought:
                        self.short_orderids = self.short(self.short_entry, self.fixed_size, True)

                elif self.short_entry != (bar.close_price - self.pricetick * self.pricetick_multilplier):
                    self.cancel_orders(self.short_orderids)

            elif self.pos > 0:
                if self.buy_orderids:
                    self.cancel_orders(self.buy_orderids)
                if self.short_orderids:
                    self.cancel_orders(self.short_orderids)

                if self.high_turning_cond1 & self.high_turning_cond2:
                    self.sell_orderids = self.sell(self.short_entry, abs(self.pos), True)

            else:
                if self.buy_orderids:
                    self.cancel_orders(self.buy_orderids)
                if self.short_orderids:
                    self.cancel_orders(self.short_orderids)

                if self.low_turning_cond1 & self.low_turning_cond2:
                    self.cover(self.long_entry, abs(self.pos), True)

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        # 只处理结束的停止单
        if stop_order.status == StopOrderStatus.WAITING:
            return
        
        # 买入停止单
        if stop_order.stop_orderid in self.buy_orderids:
            # 移除委托号
            self.buy_orderids.remove(stop_order.stop_orderid)

            # 清空停止委托价格
            if not self.buy_orderids:
                self.long_entry = 0

            # 若是撤单，且目前无仓位，则立即重发
            if stop_order.status == StopOrderStatus.CANCELLED and not self.pos:
                self.long_entry = 


        

    def cancel_orders(self, vt_orders: list):
        for vt_orderid in vt_orders:
            self.cancel_order(vt_orderid)


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