#%%
from datetime import datetime

from vnpy.app.cta_strategy.backtesting import BacktestingEngine, OptimizationSetting
from vnpy.app.cta_strategy.strategies.atr_rsi_strategy import AtrRsiStrategy

#%%
def runBacktesting():
    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol="IF888.CFFEX",
        interval="1m",
        start=datetime(2010, 1, 1),
        end=datetime(2019, 12, 30),
        rate=0.3/10000,
        slippage=0.2,
        size=300,
        pricetick=0.2,
        capital=1_000_000,
        )
    engine.add_strategy(AtrRsiStrategy, {})
    engine.load_data()
    engine.run_backtesting()
    engine.calculate_result()
    engine.calculate_statistics()
    engine.show_chart()

if __name__ == '__main__':
    runBacktesting()

# 然后在该文件夹下，按住Shift键点击鼠标右键，选择【在此处打开命令窗口】
# 或者【在此处打开PowerShell】进入命令提示符环境，并运行cProfile进行性能测试：
# python -m cProfile -o result.out 策略回测性能分析代码.py
# python -m gprof2dot -f pstats result.out | dot -Tpng -o result.png