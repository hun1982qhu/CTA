# 随着量化交易在国内金融市场越来越普及，CTA策略之间的竞争也变得越发激烈，除了体现在策略的核心交易信号方面外，也同样体现在策略的实盘委托执行中。
# 大部分vn.py官方提供的CTA策略样例中，在K线回调函数on_bar内采用的都是两步操作：
# 调用cancel_all函数，全撤之前上一根K线已经挂出的委托
# 检查核心交易信号，发出新一轮的委托挂单
# 这种简单粗暴的写法，更多是出于简化策略执行中的状态机控制，帮助vn.py初学者的降低学习难度，但由于较多的重复操作，在实盘中的运行效果未必能达到最佳。
# 好在策略模板CtaTemplate中委托函数（buy/sell/short/cover）可以直接返回委托号信息，以及on_order/on_trade回调函数会推送委托和成交状态变化，
# 结合少量的底层代码改造，我们就可以实现更加精细的Tick级别委托挂撤单管理，让策略的核心交易信号和委托执行算法更加有机地结合起来。

# 扩展OrderData对象
# 找到vn.py源代码所在的路径，使用VN Studio的情况下，
# 应该位于C:\vnstudio\Lib\site-packages\vnpy，进入到目录vnpy\trader下找到object.py 文件
# 首先需要对OrderData类进行扩展，主要表现在：
# 类的初始化除了time属性外，还增加了date和cancel_time属性
# 在__post_init__函数，增加了未成交量untraded和委托的具体日期时间datetime。
# 其中应该注意的是，由于每个行情API接口推送的时间格式不太相同，所以基于：
# 1. date格式是"%Y-%m-%d"还是"%Y%m%d";
# 2. time有无毫秒级别数据;
# 要用到4种不同的处理方法得到datetime。

@dataclass
class OrderData(BaseData):
    """
    Order data contains information for tracking lastest status
    of a specific order.
    """

    symbol: str
    exchange: Exchange
    orderid: str

    type: OrderType = OrderType.LIMIT
    direction: Direction = ""
    offset: Offset = Offset.NONE
    price: float = 0
    volume: float = 0
    traded: float = 0
    status: Status = Status.SUBMITTING

    date: str = ""
    time: str = ""
    cancel_time: str = ""

    def __post_init__(self):
        """"""
        self.vt_symbol = f"{self.symbol}.{self.exchange.value}"
        self.vt_orderid = f"{self.gateway_name}.{self.orderid}"

        self.untraded = self.volume - self.traded

        # With millisecond
        if self.date and "." in self.time:
            if "-"in self.date:
                self.datetime = datetime.strptime(" ".join([self.date, self.time]), "%Y-%m-%d %H:%M:%S.%f")
            else:
                self.datetime = datetime.strptime(" ".join([self.date, self.time]), "%Y%m%d %H:%M:%S.%f")
        # Without millisecond
        elif self.date:
            if "-" in self.date:
                self.datetime = datetime.strptime(" ".join([self.date, self.time]), "%Y-%m-%d %H:%M:%S")
            else:
                self.datetime = datetime.strptime(" ".join([self.date, self.time]), "%Y%m%d %H:%M:%S")


    def is_active(self):
        """
        Check if the order is active.
        """
        if self.status in ACTIVE_STATUSES:
            return True
        else:
            return False

    def create_cancel_request(self):
        """
        Create cancel request object from order.
        """
        req = CancelRequest(
            orderid=self.orderid, symbol=self.symbol, exchange=self.exchange
        )
        return req


# 扩展持仓明细查询

# 修改PositionHolding对象
# 进入目录vnpy\trader打开converter.py文件，这一次我们对PositionHolding类进行修改，主要改动如下：
# __init__类的初始化，新加入long_pnl，long_price，short_pnl，short_price这4个属性。即增加了持仓盈亏以及开仓均价；
# update_position函数新增缓存持仓盈亏和开仓均价；
# update_order函数首先修改了活动委托的定义，把【委托提交中】剔除，即在update_order函数只处理未成交或者部分成交状态的委托。

class PositionHolding:
    """"""

    def __init__(self, contract: ContractData):
        """"""
        self.vt_symbol = contract.vt_symbol
        self.exchange = contract.exchange

        self.active_orders = {}
        
        self.long_pos = 0
        self.long_pnl = 0
        self.long_price = 0
        self.long_yd = 0
        self.long_td = 0

        self.short_pos = 0
        self.short_pnl = 0
        self.short_price = 0
        self.short_yd = 0
        self.short_td = 0

        self.long_pos_frozen = 0
        self.long_yd_frozen = 0
        self.long_td_frozen = 0

        self.short_pos_frozen = 0
        self.short_yd_frozen = 0
        self.short_td_frozen = 0

    def update_position(self, position: PositionData):
        """"""
        if position.direction == Direction.LONG:
            self.long_pos = position.volume
            self.long_pnl = position.pnl
            self.long_price = position.price
            self.long_yd = position.yd_volume
            self.long_td = self.long_pos - self.long_yd
            self.long_pos_frozen = position.frozen
        else:
            self.short_pos = position.volume
            self.short_pnl = position.pnl
            self.short_price = position.price
            self.short_yd = position.yd_volume
            self.short_td = self.short_pos - self.short_yd
            self.short_pos_frozen = position.frozen

    def update_order(self, order: OrderData):
        """"""
        #active_orders只记录未成交和部分成交委托单
        if order.status in [Status.NOTTRADED, Status.PARTTRADED]:
            self.active_orders[order.vt_orderid] = order
        else:
            if order.vt_orderid in self.active_orders:
                self.active_orders.pop(order.vt_orderid)

        self.calculate_frozen()


# 新增get_position_detail函数
# 进入目录vnpy\app\cta_strategy打开engine.py文件，这一次我们要新增一个函数get_position_detail。
# 该函数功能就是获取我们修改后的PositionHolding对象，从而知道更加详细的持仓信息，如开仓均价，持仓盈亏等：


from collections import defaultdict, OrderedDict

    def get_position_detail(self, vt_symbol):
        """
        查询long_pos,short_pos(持仓)，long_pnl,short_pnl(盈亏),active_order(未成交字典)
        收到PositionHolding类数据
        """
        try:
            return self.offset_converter.get_position_holding(vt_symbol)
        except:
            self.write_log(f"当前获取持仓信息为：{self.offset_converter.get_position_holding(vt_symbol)},等待获取持仓信息")
            position_detail = OrderedDict()     
            position_detail.active_orders = {} 
            position_detail.long_pos = 0
            position_detail.long_pnl = 0
            position_detail.long_yd = 0
            position_detail.long_td = 0
            position_detail.long_pos_frozen = 0
            position_detail.long_price = 0
            position_detail.short_pos = 0
            position_detail.short_pnl = 0          
            position_detail.short_yd = 0
            position_detail.short_td = 0
            position_detail.short_price = 0
            position_detail.short_pos_frozen = 0
            return position_detail


# 然后，为了让交易策略能够直接从引擎调用get_position_detail函数，对CTA策略模板也得增加一个调用函数。
# 在同一目录找到template.py文件，开打后在CtaTemplate类中加入以下代码即可：

def get_position_detail(self, vt_symbol: str):
        """"""
        return self.cta_engine.get_position_detail(vt_symbol)


# 修改CTA策略代码

# 底层的功能都添加完毕了，那么现在轮到对具体交易策略逻辑进行改动，从而实现基于实时tick行情的追单和撤单。
# 添加策略运行时变量
# 包括委托状态的触发控制器、具体委托量以及拆单间隔：


def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        
        #状态控制初始化
        self.chase_long_trigger = False
        self.chase_sell_trigger = False
        self.chase_short_trigger = False
        self.chase_cover_trigger = False  
        self.long_trade_volume = 0
        self.short_trade_volume = 0
        self.sell_trade_volume = 0
        self.cover_trade_volume = 0 
        self.chase_interval = 10    #拆单间隔:秒


# 修改on_tick函数逻辑

# 需要在on_tick函数增加的对委托挂撤单管理逻辑如下：
# 调用cta策略模板新增的get_position_detail函数
# 通过engine获取活动委托字典active_orders。
# 注意的是，该字典只缓存未成交或者部分成交的委托
# 其中key是字符串格式的vt_orderid，value对应OrderData对象；
# engine取到的活动委托为空，表示委托已完成，即order_finished=True；
# 否则，表示委托还未完成，即order_finished=False，需要进行精细度管理；
# 精细管理的第一步是先处理最老的活动委托，先获取委托号vt_orderid和OrderData对象，
# 然后对OrderData对象的开平仓属性（即offst）判断是进行开仓追单还是平仓追单：
# 开仓追单情况下，先得到未成交量order.untraded
# 若当前委托超过10秒还未成交（chase_interval = 10)
# 并且没有触发追单（chase_long_trigger = False）
# 先把该委托撤销掉，然后把触发追单器启动；
# 平仓追单情况下，同样先得到未成交量，若委托超时还未成交并且平仓触发器没有启动，先撤单，然后启动平仓触发器；
# 当所有未成交委托处理完毕后，活动委托字典将清空，此时order_finished状态从False变成True，
# 用最新的买卖一档行情，该追单开仓的追单开仓，该追单平仓的赶紧平仓，每次操作后恢复委托触发器的初始状态：


def on_tick(self, tick: TickData):
        """"""
        active_orders = self.get_position_detail(tick.vt_symbol).active_orders

        if active_orders:
            #委托完成状态
            order_finished = False
            vt_orderid = list(active_orders.keys())[0]   #委托单vt_orderid
            order = list(active_orders.values())[0]      #委托单字典

            #开仓追单，部分交易没有平仓指令(Offset.NONE)
            if order.offset in (Offset.NONE, Offset.OPEN):
                if order.direction == Direction.LONG:
                    self.long_trade_volume = order.untraded
                    if (tick.datetime - order.datetime).seconds > self.chase_interval and self.long_trade_volume > 0 and (not self.chase_long_trigger) and vt_orderid:
                        #撤销之前发出的未成交订单
                        self.cancel_order(vt_orderid)
                        self.chase_long_trigger = True
                elif order.direction == Direction.SHORT:
                    self.short_trade_volume = order.untraded
                    if (tick.datetime - order.datetime).seconds > self.chase_interval and self.short_trade_volume > 0 and (not self.chase_short_trigger) and vt_orderid:  
                        self.cancel_order(vt_orderid)
                        self.chase_short_trigger = True
            #平仓追单
            elif order.offset in (Offset.CLOSE, Offset.CLOSETODAY):
                if order.direction == Direction.SHORT: 
                    self.sell_trade_volume = order.untraded
                    if (tick.datetime - order.datetime).seconds > self.chase_interval and self.sell_trade_volume > 0 and (not self.chase_sell_trigger) and vt_orderid: 
                        self.cancel_order(vt_orderid)
                        self.chase_sell_trigger = True
                if order.direction == Direction.LONG:
                    self.cover_trade_volume = order.untraded
                    if (tick.datetime - order.datetime).seconds > self.chase_interval and self.cover_trade_volume > 0 and (not self.chase_cover_trigger) and vt_orderid:                                                       
                        self.cancel_order(vt_orderid)
                        self.chase_cover_trigger = True
        else:
            order_finished = True
        if self.chase_long_trigger and order_finished:
            self.buy(tick.ask_price_1, self.long_trade_volume)
            self.chase_long_trigger = False
        elif self.chase_short_trigger and order_finished:
            self.short(tick.bid_price_1, self.short_trade_volume)
            self.chase_short_trigger = False
        elif self.chase_sell_trigger and order_finished:
            self.sell(tick.bid_price_1, self.sell_trade_volume)
            self.chase_sell_trigger = False
        elif self.chase_cover_trigger and order_finished:
            self.cover(tick.ask_price_1, self.cover_trade_volume)
            self.chase_cover_trigger = False

# 最后需要注意的是，Tick级精细挂撤单的管理逻辑，无法通过K线来进行回测检验，
# 因此通过仿真交易（比如期货基于SimNow）进行充分的测试就是重中之重了。