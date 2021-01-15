from vnpy.app.cta_strategy import(
    CtaTemplate,
    BarGenerator,
    BarData,
    )
from vnpy.trader.constant import Interval

class Cta(CtaTemplate):
    # 定义N分钟K线合成器
    self.bg5 = BarGenerator(
        self.on_bar,
        5,
        self.on_5min_bar
    )

    # 定义1小时K线合成器
    self.bg1h = BarGenerator(
        self.on_bar, 
        1,
        self.on_hour_bar,
        Interval.HOUR
    )

    

    

   

    


    

