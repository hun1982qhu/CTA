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
import numpy as np
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.base import BacktestingMode
from datetime import datetime
import numpy as np
import pandas as pd
from vnpy.trader.ui import create_qapp, QtCore
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Exchange, Interval
from vnpy.chart import ChartWidget, VolumeItem, CandleItem
from vnpy.trader.constant import Status
import numpy as np
import talib
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import style
mpl.rcParams['font.family'] = 'serif'  # 解决一些字体显示乱码的问题

style.use('ggplot')
import seaborn as sns

sns.set()

#%%
class CCIStrategy(CtaTemplate):
    """"""
    author = "Huang Ning"
    
    parameters = []

    variables = []

    def __init__(
        self,
        cta_engine: Any,
        strategy_name: str,
        vt_symbol: str,
        setting: dict,
    ):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar)
        self.am1 = NewArrayManager()

        self.k = []
        self.j = []
        self.d = []
        self.c = []

        self.original = pd.DataFrame()

    def on_init(self):
        """"""
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """"""
        self.write_log("策略启动")

    def on_stop(self):
        """"""
        self.original["k"] = self.k[-50:]
        self.original["d"] = self.d[-50:]
        self.original["j"] = self.j[-50:]
        self.original["c"] = self.c[-50]

        plt.figure(figsize=(20, 8))
        plt.plot(self.original["k"], color='r', label='k')
        plt.plot(self.original["d"], color='b', label='d')
        plt.plot(self.original["j"], color='y', label='j')
        plt.legend()
        plt.show()

        self.write_log("策略停止")
        
    def on_tick(self, tick: TickData):
        """"""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """"""
        am1 = self.am1

        am1.update_bar(bar)
        if not am1.inited:
            return

        slowk, slowd, slowj = am1.kdjs(9, array=True)

        self.k.append(slowk[-1])
        self.j.append(slowj[-1])
        self.d.append(slowd[-1])
        self.c.append(bar.close_price)


class NewArrayManager(ArrayManager):
    """"""
    def __init__(self, size=100):
        """"""
        super().__init__(size)

    def kdj(
        self, 
        fastk_period, 
        slowk_period, 
        slowk_matype, 
        slowd_period,
        slowd_matype, 
        array=False
        ):
        """"""
        slowk, slowd, = talib.STOCH(self.high, self.low, self.close, fastk_period, slowk_period, slowk_matype, slowd_period, slowd_matype)
        # 求出J值，J = (3 * D) - (2 * K)
        slowj = list(map(lambda x, y: 3*x - 2*y, slowk, slowd))
        if array:
            return slowk, slowd, slowj
        return slowk[-1], slowd[-1], slowj[-1]

    def kdjs(self, n, array=False):
        """"""
        slowk, slowd = talib.STOCH(self.high, self.low, self.close, n, 3, 0, 3, 0)
        slowj = list(map(lambda x, y: 3*x - 2*y, slowk, slowd))
        if array:
            return slowk, slowd, slowj
        return slowk[-1], slowd[-1], slowj[-1]
  
#%%
engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="rb2010.SHFE",
    interval="1m",
    start=datetime(2020, 2, 22),
    end=datetime(2020,3,10),
    rate=0.0001,
    slippage=2,
    size=10,
    pricetick=1,
    capital=1_000_000,
    mode=BacktestingMode.BAR
)
engine.add_strategy(CCIStrategy, {})
#%%
engine.load_data()
#%%
engine.run_backtesting()