from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager
)
from vnpy.app.cta_strategy.base import EngineType


class DemoStrategy4(CtaTemplate):
    """"""
    author = "黄柠"

    dc_length = 11
    trailing_percent = 0.8

    order_size = 2
    total_size = 10
    interval = 10

    dc_up = 0.0
    dc_down = 0.0
    target_pos = 0
    intra_trade_high = 0.0
    intra_trade_low = 0.0

    parameters = ["dc_length", "trailing_percent", "total_size"]
    variables = ["dc_up", "dc_down"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar, 5, self.on_5min_bar)
        self.am = ArrayManager()

        self.engine_type = self.get_engine_type()
        self.last_order_dt = None

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

        # 只有实盘交易才使用TWAP算法
        # if self.engine_type != EngineType.LIVE:
        #     return

        order_volume = self.target_pos - self.pos
        # 如果order_volume为0，即目前策略持仓已经达到目标仓位，则返回
        if not order_volume:
            return

        if self.last_order_dt:
            time_delta = tick.datetime - self.last_order_dt
            if time_delta.seconds < self.interval:
                return
        self.last_order_dt = tick.datetime

        self.cancel_all()

        if order_volume > 0:
            self.buy(tick.ask_price_1 + 10, abs(order_volume))
        elif order_volume < 0:
            self.short(tick.bid_price_1 - 10, abs(order_volume))       

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

        self.dc_up, self.dc_down = am.donchian(self.dc_length)

        # 检查信号
        if not self.pos:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            if bar.high_price >= self.dc_up:
                self.target_pos = self.total_size
            elif bar.low_price <= self.dc_down:
                self.target_pos = -self.total_size

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            long_stop = self.intra_trade_high * (1 - self.trailing_percent/100)
            if bar.low_price <= long_stop:
                self.sell(bar.close_price - 10, abs(self.pos))

        elif self.pos < 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            short_stop = self.intra_trade_low * (1 + self.trailing_percent/100)
            if bar.high_price >= short_stop:
                self.cover(bar.close_price + 10, abs(self.pos))

        self.put_event()

    def on_order(self, order: OrderData):
        """"""
        pass

    def on_trade(self, trade: TradeData):
        """"""
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """"""
        pass
