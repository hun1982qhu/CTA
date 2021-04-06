from vnpy.app.cta_strategy import(
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
    Direction
)


class BollDemoStrategyHN(CtaTemplate):
    """"""
    author = "黄柠"

    boll_window = 18
    boll_dev = 3.4
    fixed_size = 1
    atr_window = 20
    atr_multiplier = 2
    fixed_tp = 100 

    boll_up = 0.0
    boll_down = 0.0
    boll_mid = 0.0

    atr_value = 0.0
    intra_trade_high = 0.0
    long_sl = 0.0
    intra_trade_low = 0.0
    short_sl = 0.0

    long_entry = 0.0
    long_tp = 0.0
    short_entry = 0.0
    short_tp = 0.0

    parameters = [
        "boll_window", "boll_dev", 
        "fixed_size", "atr_window", "atr_multiplier",
        "fixed_tp"
    ]

    variables = [
        "boll_up", "boll_down", "boll_mid", 
        "intra_trade_high", "long_sl", 
        "intra_trade_low", "short_sl", "atr_value",
        "long_entry", "long_tp",
        "short_entry", "short_tp"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar, 15, self.on_15min_bar)
        self.am = ArrayManager()

    def on_init(self):
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.bg.update_bar(bar)

    def on_15min_bar(self, bar: BarData):
        self.cancel_all()
        
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        self.boll_up, self.boll_down = am.boll(self.boll_window, self.boll_dev)
        self.boll_mid = am.sma(self.boll_window)
        self.atr_value = am.atr(self.atr_window)

        if self.pos == 0:
            self.buy(self.boll_up, self.fixed_size, True)
            self.short(self.boll_down, self.fixed_size, True)

            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            self.long_entry = 0
            self.long_tp = 0
            self.short_entry = 0
            self.short_tp = 0


        elif self.pos > 0:
            # self.sell(self.boll_mid, abs(self.pos), True)

            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price
            
            self.long_sl = self.intra_trade_high - self.atr_value * self.atr_multiplier
            self.long_sl = max(self.boll_mid, self.long_sl)
            self.sell(self.long_sl, abs(self.pos), True)

            if self.long_tp:
                self.sell(self.long_tp, abs(self.pos))

        elif self.pos < 0:
            # self.cover(self.boll_mid, abs(self.pos), True)

            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.intra_trade_high = bar.high_price

            self.short_sl = self.intra_trade_low + self.atr_value * self.atr_multiplier
            self.short_sl = min(self.boll_mid, self.short_sl)
            self.cover(self.short_sl, abs(self.pos), True)

            if self.short_tp:
                self.cover(self.short_tp, abs(self.pos))

        self.put_event()

    def on_order(self, order: OrderData):
        self.put_event()

    def on_trade(self, trade: TradeData):
        if self.pos != 0:
            if trade.direction == Direction.LONG:
                self.long_entry = trade.price
                self.long_tp = self.long_entry + self.fixed_tp
            else:
                self.short_entry = trade.price
                self.short_tp = self.short_entry - self.fixed_tp

        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        self.put_event()













































