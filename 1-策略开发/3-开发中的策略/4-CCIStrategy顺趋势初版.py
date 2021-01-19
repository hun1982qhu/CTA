#%%
from datetime import time
from typing import Any
from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager,
    StopOrder,
    TradeData,
    OrderData
)
from vnpy.trader.object import (BarData, TickData)
from vnpy.app.cta_strategy.base import StopOrderStatus, OrderStatus
#%%
class CCIStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"
    # 定义类的参数，只能是int、float、str、bool这4种数据类型
    cci_window = 5
    fixed_size = 1
    sell_multiplier = 0.96
    cover_multiplier = 1.02
    pricetick_multilplier = 1

    # 定义类的变量，只能是int、float、str、bool这4种数据类型
    cci1 = 0.0
    cci2 = 0.0
    cci3 = 0.0

    intra_trade_high = 0.0
    intra_trade_low = 0.0
    long_entry = 0.0
    short_entry = 0.0

    parameters = [
        "cci_window",
        "fixed_size",
        "sell_multiplier",
        "cover_multiplier"
    ]
    variables = [
        "cci1",
        "cci2",
        "cci3",
        "intra_trade_high",
        "intra_trade_low",
        "long_entry",
        "short_entry"
    ]

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

        self.buy_vt_orderids = []
        self.sell_vt_orderids = []
        self.short_vt_orderids = []
        self.cover_vt_orderids = []

        self.bar_close_price = 0.0

        self.over_sold = None
        self.low_turning_cond1 = None
        self.low_turning_cond2 = None
        self.over_bought = None
        self.high_turning_cond1 = None
        self.high_turning_cond2 = None

    def on_init(self):
        """日志输出：策略初始化"""
        self.write_log("策略初始化")
        # 加载10天的历史数据用于初始化回放
        self.load_bar(10)

    def on_start(self):
        """
        当策略被启动时候调用该函数
        """
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """tick回调函数"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """K线更新"""
        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 计算CCI指标
        cci = am.cci(self.cci_window, array=True)
        self.cci1 = cci[-1]
        self.cci2 = cci[-2]
        self.cci3 = cci[-3]

        # 最低点判断条件，即生成买多开仓信号
        self.over_sold = (self.cci1 <= -100)
        self.low_turning_cond1 = (self.cci1 > self.cci2)
        self.low_turning_cond2 = (self.cci3 > self.cci2)

        # 最高点判断条件，即生成卖空开仓信号
        self.over_bought = (self.cci1 >= 100)
        self.high_turning_cond1 = (self.cci1 < self.cci2)
        self.high_turning_cond2 = (self.cci3 < self.cci2)

        self.bar_close_price = bar.close_price

        if self.pos == 0:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = bar.low_price

            # 如果此前开空仓委托都已结束
            if not self.short_vt_orderids:
                # 如果超卖，则发出开空仓限价单，同时缓存委托列表
                if self.over_sold:
                    self.short_vt_orderids = self.short(self.bar_close_price - self.get_pricetick * self.pricetick_multilplier, self.fixed_size)
            # 如果此前开空仓委托尚未全部结束
            else:
                # 遍历开空仓委托列表，撤销尚未成交委托
                for vt_orderid in self.short_vt_orderids:
                    self.cancel_order(vt_orderid)

            # 如果此前开多仓委托都已结束
            if not self.buy_vt_orderids:
                # 如果超买，则发出开多仓限价单，同时缓存委托列表
                if self.over_bought:
                    self.buy_vt_orderids = self.buy(self.bar_close_price + self.get_pricetick * self.pricetick_multilplier, self.fixed_size)
            # 如果此前多仓委托尚未全部结束
            else:
                # 遍历开多仓委托列表，撤回尚未成交委托
                for vt_orderid in self.buy_vt_orderids:
                    self.cancel_order(vt_orderid)
        elif self.pos > 0:
            self.intra_trade_high = max(self.intra_trade_high, bar.high_price)
            self.intra_trade_low = bar.low_price
            self.short_entry = self.intra_trade_high * self.sell_multiplier

            # 如果此前平多仓委托都已结束
            if not self.sell_vt_orderids:
                # 只要行情价格低于动态最高价的sell_multiplier倍就发出平多仓限价单，同时缓存委托列表
                self.sell_vt_orderids = self.sell(self.short_entry, abs(self.pos))
            # 如果此前多平仓委托尚未全部结束
            else:
                # 遍历平多仓委托列表，撤回尚未成交委托
                for vt_orderid in self.sell_vt_orderids:
                    self.cancel_order(vt_orderid)
        else:
            self.intra_trade_high = bar.high_price
            self.intra_trade_low = min(self.intra_trade_low, bar.low_price)

            self.long_entry = self.intra_trade_low * self.cover_multiplier

            # 如果此前平空仓委托都已结束
            if not self.cover_vt_orderids:
                # 只要行情价格高于动态最低价的cover_multiplier倍就发出平空仓限价单，同时缓存委托列表
                self.cover_vt_orderids = self.cover(self.long_entry, abs(self.pos))
        # 更新图形界面
        self.put_event()

    def on_trade(self, trade: TradeData):
        """"""
        self.put_event()

    def on_order(self, order: OrderData):
        """"""
        # 只处理已撤销或者已触发的委托，如果委托状态为“等待中”，则直接返回
        if order.status == OrderStatus.WAITING:
            return

        # 移除已经结束的委托号
        for buf_orderids in [
            self.buy_vt_orderids,
            self.sell_vt_orderids,
            self.short_vt_orderids,
            self.cover_vt_orderids
        ]:
            if order.orderid in buf_orderids:
                buf_orderids.remove(order.orderid)

        # 发出新的委托
        if self.pos == 0:
            # 如果此前开空仓委托都已结束
            if not self.short_vt_orderids:
                # 如果超卖，则发出开空仓限价单，同时缓存委托列表
                if self.over_sold:
                    self.short_vt_orderids = self.short(self.bar_close_price - self.get_pricetick * self.pricetick_multilplier, self.fixed_size)

            # 如果此前开多仓委托都已结束
            if not self.buy_vt_orderids:
                # 若果超买和最高拐点同时出现，则发出开空仓停止单，同时缓存委托列表
                if self.over_bought:
                    self.buy_vt_orderids = self.buy(self.bar_close_price + self.get_pricetick * self.pricetick_multilplier, self.fixed_size)

        if self.pos > 0:
            # 如果此前平多仓委托都已结束
            if not self.sell_vt_orderids:
                # 只要行情价格低于动态最高价的sell_multiplier倍就发出平多仓限价单，同时缓存委托列表
                    self.sell_vt_orderids = self.sell(self.short_entry, abs(self.pos))

        else:
            # 如果此前平空仓委托都已结束
            if not self.cover_vt_orderids:
                # 只要行情价格高于动态最高价的cover_multiplier倍就发出平空仓限价单，同时缓存委托列表
                self.cover_vt_orderids = self.cover(self.long_entry, abs(self.pos))

        self.put_event


    