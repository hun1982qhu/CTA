from datetime import datetime

from vnpy.trader.object import HistoryRequest
from vnpy.trader.database import database_manager
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.rqdata import rqdata_client
from vnpy.trader.setting import SETTINGS


interval = Interval.MINUTE
symbol = "IF888"
exchange = Exchange.CFFEX

start = datetime(2020, 1, 1)



n = rqdata_client.init(SETTINGS["rqdata.username"], SETTINGS["rqdata.password"])

if n:
    print("RQData登录成功")
else:
    print("RQData登录失败")

# 从米筐下载数据
req = HistoryRequest(
    symbol,
    exchange,
    start,
    datetime.now(),
    interval=interval
)


data =  rqdata_client.query_history(req)

print(data)