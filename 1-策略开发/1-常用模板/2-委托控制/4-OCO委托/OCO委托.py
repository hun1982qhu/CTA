# 1 策略原理

# KingKeltner策略是一个典型的通道突破策略，即当价格突破通道上轨时做多，当价格走低突破通道下轨时做空。轨道计算的思路也相对简单，先计算移动均线（MA），并且统计ATR指标，设置一定的通道宽度偏差X，如下：

# 上轨=MA+X*ATR
# 下轨=MA-X*ATR
# 因为ATR指标的性质，相对于标准差，它能够捕捉到K线跳空高开或者跳空低开的情况，所以更适合于一些在短期内有较大波动的品种，如股指期货，或者有小股指之称的螺纹钢。

# KingKeltner策略三大要素

# 信号：价格突破上轨做多，突破下轨做空

# 过滤：若价格在通道内上下走动，则不进行开仓操作

# 出场：固定百分点数移动止损离场

# 2 策略代码解释

# 1）策略参数
# KingKeltner通道指标初始化天数是11天，调用K线管理模块上ta-lib库定义的函数可以计算出均线和ATR指标，进而得出KingKeltner的上轨和下轨，代码如下：
def keltner(self, n, dev, array=False):
        """肯特纳通道"""
        mid = self.sma(n, array)
        atr = self.atr(n, array)
        
        up = mid + atr * dev
        down = mid - atr * dev
        
        return up, down
# 策略参数
    kkLength = 11           # 计算通道中值的窗口数
    kkDev = 1.6             # 计算通道宽度的偏差
    trailingPrcnt = 0.8     # 移动止损
    initDays = 10           # 初始化数据所用的天数
    fixedSize = 1           # 每次交易的数量

# 在上面是Keltner函数中，入参是初始化天数（kkLeng）与通道宽度偏差（kkDev），然后把array设置为True，这样就可以计算出一系列通道上轨（kkUp）和通道下轨（kkDown）。
# 移动止损设置为0.8%，即在最高点回落0.8%或者在最低点反弹0.8%瞬间用停止单平仓离场
# 策略初始化所需要载入的天数是10，且每次交易的合约数量为1手

# 2）新的委托方式：OCO

# OCO委托全称是One-Cancels-the-Other Order，意思是二选一委托。即在K线内同时发出止损买单和止损卖单：

# 若价格突破上轨，触发止损买单同时取消止损卖单
# 若价格突破下轨，触发止损卖单同时取消止损买单
# 这种挂单方式在国内交易所比较少见，一般多用于外汇市场，因为货币对在短时间内会有很强的震荡，比较难判断趋势，这时候OCO的优点就彰显出来了，当盘整震荡的行情接近结束，而要进入到一个上升或下降的趋势时，可利用OCO挂单捕捉趋势。一个例子是发生重大行情如非农或者利率决议公布，若不确定接下来的行情，可利用OCO委托进行挂单。

# OCO委托流程如下：
# 创建3个空的列表：buyOrderIDList、shortOrderIDList和ordList。
# buyOrderIDList用于缓存止损买入单的委托，分别插入委托价格，合约手数
# shortOrderIDList用于缓存止损卖出单的委托，分别插入委托价格，合约手数
# ordList用于缓存所有发出的委托单子，用extend（）的方法把上面2个列表添加进来
#------------------------------------------------------------------------
# 策略变量
buyOrderIDList = []                 # OCO委托买入开仓的委托号
shortOrderIDList = []               # OCO委托卖出开仓的委托号
orderList = []                      # 保存委托代码的列表
#--------------------------------------------------------------------------------
def sendOcoOrder(self, buyPrice, shortPrice, volume):
    """
    发送OCO委托
    OCO(One Cancel Other)委托：
    1. 主要用于实现区间突破入场
    2. 包含两个方向相反的停止单
    3. 一个方向的停止单成交后会立即撤消另一个方向的
    """
    # 发送双边的停止单委托，并记录委托号
    self.buyOrderIDList = self.buy(buyPrice, volume, True)
    self.shortOrderIDList = self.short(shortPrice, volume, True)
    
    # 将委托号记录到列表中
    self.orderList.extend(self.buyOrderIDList)
    self.orderList.extend(self.shortOrderIDList)

# 3） OCO发单与平仓
# 为保证委托的唯一性，同样要撤销之前尚未成交的委托，但这一次不用cancelAll（）的方法，先在orderList列表中遍历出orderID，然后删除掉，以保证清空orderList的目标。
# 调用K线管理模块ArrayManager里面updateBar（bar）函数把1分钟K线数据合成5分钟K线。检查K线数据若不够多，则直接返回不进行下面操作。
# 计算KingKeltner通道的上下轨，若当前无持仓，用最新的5分钟K线数据初始化持仓期的最高点（intraTradeeHigh）和最低点（intraTradeLow），用OCO委托在上下轨道挂上突破停止单，进行开仓操作，并且缓存停止单委托到buyOrderIDList和shortOrderIDList中：
# 若价格往上走，触发停止买单成交，开仓做多。 调用Max（）函数统计日高点，作用是设置固定百分比的移动止损离场，平仓委托l也需要缓存到orderList列表中。由于OCO委托的特点， 多头开仓成交后，撤消空头委托，方法在shortOrderIDList中遍历shortOrderID，然后用cancel（）的方法从列表中移除。
# 若价格往下走，触发止损卖单成交，开仓做空。同理调用Min（）统计出日低点，设置离场点，发出停止买单（Stop=True），并且缓存该委托到orderList列表中。空头开仓成交后，撤消多头委托，即遍历buyOrderIDList，用cancel （）移除其对应的buyOrderID。

def onFiveBar(self, bar):
        """收到5分钟K线"""
        # 撤销之前发出的尚未成交的委托（包括限价单和停止单）
        for orderID in self.orderList:
            self.cancelOrder(orderID)
        self.orderList = []
    
        # 保存K线数据
        am = self.am
        am.updateBar(bar)
        if not am.inited:
            return
        
        # 计算指标数值
        self.kkUp, self.kkDown = am.keltner(self.kkLength, self.kkDev)
        
        # 判断是否要进行交易
    
        # 当前无仓位，发送OCO开仓委托
        if self.pos == 0:
            self.intraTradeHigh = bar.high
            self.intraTradeLow = bar.low            
            self.sendOcoOrder(self.kkUp, self.kkDown, self.fixedSize)
    
        # 持有多头仓位
        elif self.pos > 0:
            self.intraTradeHigh = max(self.intraTradeHigh, bar.high)
            self.intraTradeLow = bar.low
            
            l = self.sell(self.intraTradeHigh*(1-self.trailingPrcnt/100), 
                          abs(self.pos), True)
            self.orderList.extend(l)
    
        # 持有空头仓位
        elif self.pos < 0:
            self.intraTradeHigh = bar.high
            self.intraTradeLow = min(self.intraTradeLow, bar.low)
            
            l = self.cover(self.intraTradeLow*(1+self.trailingPrcnt/100), 
                           abs(self.pos), True)
            self.orderList.extend(l)
    
        # 同步数据到数据库
        self.saveSyncData()    
    
        # 发出状态更新事件
        self.putEvent()    

#---------------------------------------------------
def onTrade(self, trade):
    if self.pos != 0:
        # 多头开仓成交后，撤消空头委托
        if self.pos > 0:
            for shortOrderID in self.shortOrderIDList:
                self.cancelOrder(shortOrderID)
        # 反之同样
        elif self.pos < 0:
            for buyOrderID in self.buyOrderIDList:
                self.cancelOrder(buyOrderID)
        
        # 移除委托号
        for orderID in (self.buyOrderIDList + self.shortOrderIDList):
            if orderID in self.orderList:
                self.orderList.remove(orderID)
            
    # 发出状态更新事件
    self.putEvent()

# 设置回测使用的数据
# engine.setBacktestingMode(engine.BAR_MODE)    # 设置引擎的回测模式为K线
# engine.setDatabase(MINUTE_DB_NAME, 'IF0000')  # 设置IF股指期货
# engine.setStartDate('20100416')               # 设置回测用的数据起始日期
# engine.setEndDate('20180101')                 # 设置回测用的数据结束日期
# 配置回测引擎参数
# engine.setSlippage(0.2)     # 设置滑点为股指1跳
# engine.setRate(0.5/10000)   # 设置手续费万0.5
# engine.setSize(300)         # 设置股指合约大小 
# engine.setPriceTick(0.2)    # 设置股指最小价格变动   
# engine.setCapital(1000000)  # 设置回测本金