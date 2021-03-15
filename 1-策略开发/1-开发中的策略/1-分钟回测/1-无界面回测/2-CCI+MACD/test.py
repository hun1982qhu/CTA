import talib
import numpy as np
from vnpy.trader.utility import ArrayManager

am = ArrayManager()

ema = talib.EMA(np.array([1.00, 2.00, 3.00, 4.00, 5.00]), timeperiod=5)
print(round(ema[-1], 2))
ma = talib.MA(np.array([1.00, 2.00, 3.00, 4.00, 5.00]), timeperiod=5, matype=0)
print(ma)