from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarData,
    StopOrder,
    TickData,
    TradeData,
    Direction,
    ArrayManager
)
from vnpy.app.cta_strategy.xsecbar import XsecBarGenerator
from vnpy.app.cta_strategy.base import (StopOrderStatus)
from vnpy.trader.object import (OrderData, BarData)


class BollAtrStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"

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

    parameters = [
        "boll_window",
        "boll_dev",
        "fixed_size",
        "atr_window",
        "atr_multiplier",
        "fixed_tp"
    ]
    variables = [
       "boll_up",
       "boll_down",
       "boll_mid",
       "atr_value",
       "intra_trade_high",
       "long_sl",
       "intra_trade_low",
       "short_sl"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        # update_tick函数用于合成1分钟K线，但在此处改为以50秒作为1分钟K线切分点
        self.bg = XsecBarGenerator(self.on_bar)
        self.am = ArrayManager()

        # 用于细粒度委托控制
        self.buy_vt_orderids = []
        self.sell_vt_orderids = []
        self.short_vt_orderids = []
        self.cover_vt_orderids = []

        self.buy_price = 0.0
        self.sell_price = 0.0
        self.short_price = 0.0
        self.cover_price = 0.0

        self.last_bar = None

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
        """
        on_bar函数中得到的K线推送，即以50秒为切分点的分钟K线
        """
        # 时间序列指标计算器初始化
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算布林带的上轨、下轨、中轨和atr值
        self.boll_up, self.boll_down = am.boll(self.boll_window, self.boll_dev)
        self.boll_mid = am.sma(self.boll_window)
        self.atr_value = am.atr(self.atr_window)

        # 生成交易信号
        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            self.buy_price = self.boll_up
            self.sell_price = 0.0
            self.short_price = self.boll_down
            self.cover_price = 0.0

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

        # 根据以上交易信号执行挂撤交易
        # 当持仓为0时
        if self.pos == 0:
            # 如果之前的买入开仓委托都已经结束
            if not self.buy_vt_orderids:
                # 如果存在买入开仓交易信号
                if self.buy_price:
                    self.buy_vt_orderids = self.buy(self.buy_price, self.fixed_size, True)
                    self.buy_price = 0.0  # 执行需要清空信号
            else:
                # 遍历买入开仓委托列表，将尚未成交的委托撤单
                for vt_orderid in self.buy_vt_orderids:
                    self.cancel_order(vt_orderid)

            # 如果之前的卖出开仓委托都已经结束
            if not self.short_vt_orderids:
                # 如果存在卖出开仓信号
                if self.short_price:
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    self.short_price = 0.0
            else:
                # 遍历卖出开仓委托列表，将尚未成交的委托撤单
                for vt_orderid in self.short_vt_orderids:
                    self.cancel_order(vt_orderid)

        # 当持多仓时
        elif self.pos > 0:
            # 如果之前的卖出平仓委托都已经结束
            if not self.sell_vt_orderids:
                # 如果存在卖出平仓信号
                if self.sell_price:
                    self.sell_vt_orderids = self.sell(self.sell_price, abs(self.pos), True)
                    self.sell_price = 0.0
            else:
                # 遍历卖出平仓委托列表，将未成交的委托撤单
                for vt_orderid in self.sell_vt_orderids:
                    self.cancel_order(vt_orderid)
        else:
            if not self.cover_vt_orderids:
                if self.cover_price:
                    self.cover_vt_orderids = self.cover(self.cover_price, abs(self.pos), True)
            else:
                for vt_orderid in self.cover_vt_orderids:
                    self.cancel_order(vt_orderid)

        self.put_event()

    def on_order(self, order: OrderData):
        """"""
        pass

    def on_trade(self, trade: TradeData):
        """"""
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """"""
        # 测试stop_order的状态
        print(stop_order.__dict__)
        # 只处理撤销或者触发的停止委托单
        if stop_order.status == StopOrderStatus.WAITING:
            return

        # 移除已经结束的停止委托单
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
                    self.buy_price = 0.0

            if not self.short_vt_orderids:
                if self.short_price:
                    self.short_vt_orderids = self.short(self.short_price, self.fixed_size, True)
                    self.short_price = 0.0

        elif self.pos > 0:
            if not self.sell_vt_orderids:
                if not self.sell_price:
                    self.sell_vt_orderids = self.sell(self.sell_price, abs(self.pos), True)
                    self.sell_price = 0.0

        else:
            if not self.cover_vt_orderids:
                if not self.cover_price:
                    self.cover_vt_orderids = self.cover(self.cover_price, abs(self.pos), True)
                    self.cover_price = 0.0

