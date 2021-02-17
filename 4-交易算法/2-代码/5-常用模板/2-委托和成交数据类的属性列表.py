# 委托管理相关的所有内容
from vnpy.trader.object import OrderData, OrderRequest, Status, PositionData, AccountData, ContractData, TradeData, ACTIVE_STATUSES
from vnpy.trader.constant import Offset, Status, OrderType, Exchange, Interval
from vnpy.trader.converter import PositionHolding
from vnpy.app.cta_strategy.base import StopOrder, StopOrderStatus
# 委托订单类型


order1 = OrderData()
order1.vt_orderid
order1.vt_symbol
order1.status
order1.gateway_name
order1.orderid
order1.datetime
order1.status = Status.ALLTRADED
order1.status = Status.CANCELLED
order1.status = Status.PARTTRADED
order1.status = Status.REJECTED
order1.status = Status.SUBMITTING
order1.is_active = ACTIVE_STATUSES

stop_order1 = StopOrder()
stop_order1.stop_orderid
stop_order1.vt_orderids
stop_order1.vt_symbol
stop_order1.status = StopOrderStatus.WAITING
stop_order1.status = StopOrderStatus.TRIGGERED
stop_order1.status = StopOrderStatus.CANCELLED

trade_data1 = TradeData()
trade_data1.orderid
trade_data1.vt_orderid
trade_data1.tradeid
trade_data1.offset
trade_data1.direction
trade_data1.exchange
trade_data1.gateway_name
trade_data1.price
trade_data1.volume
trade_data1.datetime
trade_data1.orderid
trade_data1.vt_orderid

postiondata1 = PositionData
postiondata1.frozen

positionholding1 = PositionHolding()
positionholding1.active_orders