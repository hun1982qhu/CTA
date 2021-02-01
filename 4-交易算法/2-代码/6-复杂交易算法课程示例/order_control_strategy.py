from vnpy.app.cta_strategy import (
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

from vnpy.app.cta_strategy.base import StopOrderStatus


class OrderDemoStrategy(CtaTemplate):
    """"""
    author = "用Python的交易员"

    boll_window = 18
    boll_dev = 3.4
    fixed_size = 1
    atr_window = 20
    atr_multiplier = 2

    boll_up = 0
    boll_down = 0
    boll_mid = 0
    
    atr_value = 0
    intra_trade_high = 0
    long_sl = 0
    intra_trade_low = 0
    short_sl = 0

    long_entry = 0
    short_entry = 0

    parameters = [
        "boll_window", "boll_dev", 
        "fixed_size", 
        "atr_window", "atr_multiplier"
    ]
    variables = [
        "boll_up", "boll_down", "boll_mid",
        "atr_value",
        "intra_trade_high", "long_sl",
        "intra_trade_low", "short_sl"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar, 15, self.on_15min_bar)
        self.am = ArrayManager()

        self.buy_vt_orderids = []
        self.sell_vt_orderids = []
        self.short_vt_orderids = []
        self.cover_vt_orderids = []

        self.buy_price = 0
        self.sell_price = 0
        self.short_price = 0
        self.cover_price = 0

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

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_15min_bar(self, bar: BarData):
        """"""
        # 生成交易信号
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return
        
        self.boll_up, self.boll_down = am.boll(self.boll_window, self.boll_dev)
        self.boll_mid = am.sma(self.boll_window)
        self.atr_value = am.atr(self.atr_window)
        
        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            self.buy_price = self.boll_up
            self.sell_price = 0
            self.short_price = self.boll_down
            self.cover_price = 0

        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price

            self.long_sl = self.intra_trade_high - self.atr_value * self.atr_multiplier
            self.long_sl = max(self.boll_mid, self.long_sl)

            self.buy_price = 0
            self.sell_price = self.long_sl
            self.short_price = 0
            self.cover_price = 0

        elif self.pos < 0:
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)
            self.intra_trade_high = bar.high_price

            self.short_sl = self.intra_trade_low + self.atr_value * self.atr_multiplier
            self.short_sl = min(self.boll_mid, self.short_sl)

            self.buy_price = 0
            self.sell_price = 0
            self.short_price = 0
            self.cover_price = self.short_sl

        # 根据信号执行挂撤交易
        if self.pos == 0:
            # 检查之前委托都已经结束
            if not self.buy_vt_orderids:
                # 检查存在信号
                if self.buy_price:
                    self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
                    self.buy_price = 0      # 执行需要清空信号
            else:
                # 遍历委托号列表撤单
                for vt_orderid in self.buy_vt_orderids:
                    self.cancel_order(vt_orderid)
            
            if not self.short_vt_orderids:
                if self.short_price:
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    self.short_price = 0
            else:
                for vt_orderid in self.short_vt_orderids:
                    self.cancel_order(vt_orderid)
        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if self.sell_price:
                    self.sell_vt_orderids = self.sell(self.sell_price, abs(self.pos), True)
                    self.sell_price = 0
            else:
                for vt_orderid in self.sell_vt_orderids:
                    self.cancel_order(vt_orderid)
        else:
            if not self.cover_vt_orderids:
                if self.cover_price:
                    self.cover_vt_orderids = self.cover(self.cover_price, abs(self.pos), True)
                    self.cover_price = 0
            else:
                for vt_orderid in self.cover_vt_orderids:
                    self.cancel_order(vt_orderid)

        # Update UI
        self.put_event()

    def on_order(self, order: OrderData):
        """
        Callback of new order data update.
        """
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        # 如果发出的是停止单，委托状态的回调只能写在on_stop_order下
        # 只处理撤销或者触发的停止单委托
        if stop_order.status == StopOrderStatus.WAITING:
            return

        # 移除已经结束的停止单委托号
        for buf_orderids in [
            self.buy_vt_orderids,
            self.sell_vt_orderids,
            self.short_vt_orderids,
            self.cover_vt_orderids
        ]:
            if stop_order.stop_orderid in buf_orderids:
                buf_orderids.remove(stop_order.stop_orderid)
        
        # 发出新的委托
        if self.pos == 0:
            if not self.buy_vt_orderids:
                if self.buy_price:
                    self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
                    self.buy_price = 0
            
            if not self.short_vt_orderids:
                if self.short_price:
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    self.short_price = 0
            
        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if self.sell_price:
                    self.sell_vt_orderids = self.sell(self.sell_price, abs(self.pos), True)
                    self.sell_price = 0
            
        else:
            if not self.cover_vt_orderids:
                if self.cover_price:
                    self.cover_vt_orderids = self.cover(self.cover_price, abs(self.pos), True)
                    self.cover_price = 0

