from typing import Any
from vnpy.app.cta_strategy import (
    CtaTemplate,
    BarGenerator,
    ArrayManager
)
from vnpy.trader.object import (
    BarData,
    TickData
)

# 定义自己的策略类
class DemoStragety(CtaTemplate):
    """"""
    # 1、策略作者
    author = "H.N."
    # 2、定义类的参数
    fast_window = 10
    slow_window = 20

    
    # 3、定义类的变量
    fast_ma0 = 0.0
    fast_ma1 = 0.0
    slow_ma0 = 0.0
    slow_ma1 = 0.0

    parameters =[
        "fast_window",
        "slow_window"
    ]
    variables =[
        "fast_ma0",
        "fast_ma1",
        "slow_ma0",
        "slow_ma1",
    ]
    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        # 调用父类的初始化函数传进去，帮助策略模板实现初始化
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()


    def on_init(self):
        """日志输出：策略初始化"""
        self.write_log("策略初始化")
        # 加载10天的历史数据用于初始化回放
        self.load_bar(30)

    def on_start(self):
        """
        当策略被启动时候调用该函数
        """
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_tick(self,tick:TickData):
        """TICK更新"""
        self.bg.update_tick(tick)

    def on_bar(self, bar:BarData):
        """K线更新"""
        am =self.am

        am.update_bar(bar)
        if not am.inited:
            return
        
        # 计算技术指标
        # # array =True 返回数组
        fast_ma =am.sma(self.fast_window,array=True)
        self.fast_ma0 =fast_ma[-1]
        self.fast_ma1 =fast_ma[-2]

        slow_ma = am.sma(self.slow_window,array=True)
        self.slow_ma0 =slow_ma[-1]
        self.slow_ma1 =slow_ma[-2]

        # 判断均线交叉
        cross_over =(self.fast_ma0 >= self.slow_ma0 and
                        self.fast_ma1 < self.slow_ma1)
        cross_below = (self.fast_ma0 <= self.slow_ma0 and 
                        self.fast_ma1 > self.slow_ma1)

        # 金叉的情况
        if cross_over:
            price =bar.close_price + 5 

            if not self.pos:
                self.buy(price,1)
            elif self.pos<0: 
                self.cover(price,1)
                self.buy(price,1)
        elif cross_below:
            price = bar.close_price - 5

            if not self.pos:
                self.sell(price,1)
            elif self.pos>0:
                self.sell(price,1)
                self.short(price,1)
        # 更新图形界面
        self.put_event()

   
