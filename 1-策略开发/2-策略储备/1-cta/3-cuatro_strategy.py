from vnpy.app.cta_strategy import(
    CtaTemplate,
    BarGenerator,
    ArrayManager,
    TickData,
    BarData,
    OrderData,
    TradeData,
    StopOrder
    )
from bargeneratorHN import MyGenerator
from typing import Any
from vnpy.app.cta_strategy.base import EngineType


class CuatroStrategy(CtaTemplate):
    """"""

    author = "黄柠"

    # 定义参数
    boll_window = 20
    boll_dev = 2.0
    rsi_window = 14
    rsi_signal = 30
    fast_window = 5
    slow_window = 20
    trailing_long = 1.0
    trailing_short = 1.0
    fixed_size = 1

    # 定义变量
    boll_up = 0.0
    boll_down = 0.0
    rsi_value = 0.0
    rsi_long = 0.0
    rsi_short = 0.0
    fast_ma = 0.0
    slow_ma = 0.0
    ma_trend = 0
    intra_trade_high = 0.0
    intra_trade_low = 0.0
    long_stop = 0.0
    short_stop = 0.0

    parameters = [
        "boll_window",
        "boll_dev",
        "rsi_window", 
        "rsi_signal", 
        "fast_window",
        "slow_window", 
        "trailing_long",
        "trailing_short",
        "fixed_size"
    ]

    variables = [
        "boll_up",
        "boll_down",
        "rsi_value",
        "rsi_long",
        "rsi_short",
        "fast_ma",
        "slow_ma",
        "ma_trend",
        "intra_trade_high",
        "intra_trade_low",
        "long_stop",
        "short_stop"
    ]

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.rsi_long = 50 + self.rsi_signal
        self.rsi_short = 50 - self.rsi_signal
        
        self.bg5 = BarGenerator(self.on_bar, 5, self.on_5min_bar)
        self.bg15 = BarGenerator(self.on_bar, 15, self.on_15min_bar)

        self.am5 = ArrayManager()
        self.am15 = ArrayManager()

    
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
        self.bg5.update_tick(tick)

    
    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg5.update_bar(bar)
        self.bg15.update_bar(bar)


    def on_5min_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.cancel_all()

        self.am5.update_bar(bar)
        if not self.am5.inited or not self.am15.inited:
            return

        self.boll_up, self.boll_down = self.am5.boll(self.boll_window, self.boll_dev)
        self.rsi_value = self.am5.rsi(self.rsi_window)
        boll_width = self.boll_up - self.boll_down

        engine_type = self.get_engine_type()

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low =  bar.low_price
            self.long_stop = 0
            self.short_stop = 0

            if self.ma_trend > 0 and self.rsi_value >= self.rsi_long:
                if engine_type == EngineType.BACKTESTING:
                    self.buy(self.boll_up, self.fixed_size, stop=True)
                else:
                    self.buy(self.boll_up, self.fixed_size, stop=True, lock=True)

            if self.ma_trend <= 0 and self.rsi_value <= self.rsi_short:
                if engine_type == EngineType.BACKTESTING:
                    self.short(self.boll_down, self.fixed_size, stop=True)
                else:
                    self.short(self.boll_down, self.fixed_size, stop=True, lock=True)

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.long_stop = (self.intra_trade_high - self.trailing_long * boll_width)
            self.sell(self.long_stop, abs(self.pos), stop=True)
            
        else:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.short_stop= (self.intra_trade_low + self.trailing_short * boll_width)
            self.cover(self.short_stop, abs(self.pos), stop=True)

        self.put_event()


    def on_15min_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.am15.update_bar(bar)
        if self.am15.inited:
            return

        self.fast_ma = self.am15.sma(self.fast_window)
        self.slow_ma =  self.am15.sma(self.slow_window)

        if self.fast_ma > self.slow_ma:
            self.ma_trend = 1
        elif self.fast_ma <= self.slow_ma:
            self.ma_trend = 0

        self.put_event()


    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    
    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        self.put_event()

    
    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        self.put_event()

    