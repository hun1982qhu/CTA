#%%
from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.strategies.CCIStrategy import (CCIStrategy)
from vnpy.app.cta_strategy.base import BacktestingMode
from datetime import datetime
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
#%%
engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="rb888.SHFE",
    interval="1m",
    start=datetime(2020, 2, 10),
    end=datetime(2020, 7, 12),
    rate=0.000,
    slippage=0.2,
    size=1,
    pricetick=0.2,
    capital=1_000_000,
    mode=BacktestingMode.BAR
)
engine.add_strategy(CCIStrategy, {})
#%%
engine.load_data()
engine.run_backtesting()
#%%
engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()
#%%
# setting = OptimizationSetting()
# setting.set_target("end_balance")
# setting.add_parameter("cci_window", 5, 1, 15)
# setting.add_parameter("sell_multipliaer", 0.88, 0.01, 0.99)
# setting.add_parameter("cover_multiplier", 1.01, 0.01, 1.09)

# engine.run_ga_optimization(setting)
# %%
