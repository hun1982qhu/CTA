from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)

from bull_bear import calculate_bull_bear_line
from pnl_tool import PnlTracker


class DemoStrategy(CtaTemplate):
    """"""
    author = "用Python的交易员"

    bull_bear_window = 30
    pnl_window = 20
    fixed_size = 5

    bull_bear_value = 0
    pnl_ma = 0
    pnl_value = 0

    parameters = ["bull_bear_window", "pnl_window"]
    variables = ["bull_bear_value", "pnl_ma", "pnl_value"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super(DemoStrategy, self).__init__(
            cta_engine, strategy_name, vt_symbol, setting
        )

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()
        self.tracker = PnlTracker(1000)

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
        # 虚拟交易的成交撮合
        self.tracker.on_bar(bar)

        # 撤单之前所有的委托
        self.cancel_all()
        self.tracker.cancel_all()   # 每根K线撤销全部虚拟委托

        # 更新K线条容器
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算牛熊线
        self.bull_bear_value = calculate_bull_bear_line(
            self.am.close, self.bull_bear_window)

        # 获取虚拟交易的净值情况
        balance_array = self.tracker.get_balance_array(self.pnl_window)
        balance_ma = balance_array.mean()
        balance_value = self.tracker.get_last_balance()

        # 判断真实交易的执行
        # 虚拟净值高于均线，则采纳信号
        if balance_value > balance_ma:
            if not self.pos:
                if bar.close_price > self.bull_bear_value:
                    self.buy(bar.close_price+10, self.fixed_size)
                elif bar.close_price < self.bull_bear_value:
                    self.short(bar.close_price-10, self.fixed_size)
            if self.pos > 0:
                if bar.close_price < self.bull_bear_value:
                    self.sell(bar.close_price-10, self.fixed_size)
            else:
                if bar.close_price > self.bull_bear_value:
                    self.cover(bar.close_price+10, self.fixed_size)
        # 否则，如有仓位立即止损
        else:
            if self.pos > 0:
                self.sell(bar.close_price-10, self.fixed_size)
            elif self.pos < 0:
                self.cover(bar.close_price+10, self.fixed_size)

        # 虚拟委托判断
        # 当前没有持仓时
        if not self.tracker._pos:
            # 最新K线收盘价大于牛熊线，则做多
            if bar.close_price > self.bull_bear_value:
                self.tracker.buy(bar.close_price+10, self.fixed_size)
            # 最新K线收盘价小于牛熊线，则做空
            elif bar.close_price < self.bull_bear_value:
                self.tracker.short(bar.close_price-10, self.fixed_size)
        # 多头持仓
        elif self.tracker._pos > 0:
            # 最新K线收盘价小于牛熊线，则平多
            if bar.close_price < self.bull_bear_value:
                self.tracker.sell(bar.close_price-10, self.fixed_size)
        else:
            # 最新K线收盘价大于牛熊线，则平空
            if bar.close_price < self.bull_bear_value:
                self.tracker.cover(bar.close_price+10, self.fixed_size)

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
        pass
