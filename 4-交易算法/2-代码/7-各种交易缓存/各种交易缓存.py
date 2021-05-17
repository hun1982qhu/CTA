from vnpy.app.cta_strategy.engine import CtaEngine
from vnpy.app.cta_strategy.base import StopOrder
from vnpy.trader.object import OrderData
from vnpy.tra

ctaengine = CtaEngine()

ctaengine.strategy_orderid_map  # strategy_name: orderid list
ctaengine.orderid_strategy_map # vt_orderid: strategy
ctaengine.symbol_strategy_map  # vt_symbol: strategy list
ctaengine.stop_orders  # stop_orderid: stop_order
ctaengine.strategies  # strategy_name: strategy

# 以下用于说明oderid和vt_orderid的区别

order = OrderData()
orderid = order.orderid
vt_orderid = f"{self.gateway_name}.{self.orderid}"

stoporder = StopOrder()
stoporder.vt_orderids