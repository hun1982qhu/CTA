# 回归到正题，vn.py中的K线合成器工具BarGenerator（位于vnpy.trader.utility模块下）
# 从Tick合成K线的标准逻辑是对当前时间戳的分钟数字求余来进行切片的，具体代码如下：

if self.interval == Interval.MINUTE:
    # x-minute bar
    if not (bar.datetime.minute + 1) % self.window:
        finished = True

# 要准确的把60分钟完整切片到等份，切片区间必须是以下这些能够整除60的数字：

# 2、3、5、6、10、15、20、30

# 但对于商品期货来说，由于上午的15分钟休盘，会导致某些情况下合成K线数据的不正确。

# 以20分钟为例，正常应该在每小时的19分、39分和59分的分钟线走完时合成20分钟K线。因为10:19的分钟数据不存在（休盘时间），不会触发切片合成，而要等到10:39分才会触发，导致这跟K线中会包含10:00-10:14和10:30-10:49两段共计35分钟的数据，和交易策略中预期的逻辑不符。

# 解决方案也很简单，只需对三大商品期货交易所的品种都进行一条特殊的逻辑处理，当收到上午10:14的分钟数据更新时我们立刻进行切分，这样下一根K线中的数据就一定从10点30分开始了：

if self.interval == Interval.MINUTE:
    # x-minute bar
    if not (bar.datetime.minute + 1) % self.window:
        finished = True
    elif (
        bar.datetime.time() == time(10, 14)
        and bar.exchange in [
            Exchange.SHFE, Exchange.DCE, Exchange.CZCE
        ]
    ):
        finished = True