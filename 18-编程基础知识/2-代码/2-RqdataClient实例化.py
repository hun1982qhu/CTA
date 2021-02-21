#%%
from vnpy.trader.rqdata import RqdataClient
from vnpy.trader.object import BarData, HistoryRequest
from vnpy.trader.constant import Exchange, Interval
from datetime import datetime
import time
import pandas as pd
from pandas.core.frame import DataFrame
#%%
rqdata_client = RqdataClient()
a = rqdata_client.init(username="13581903798", password="hun829248")
rq_symbol1 = rqdata_client.to_rq_symbol("rb2010", Exchange.SHFE)
start_time = datetime.strptime("2019-09-01 09:00:00", "%Y-%m-%d %H:%M:%S").date()
end_time = datetime.strptime("2020-09-01 09:00:00", "%Y-%m-%d %H:%M:%S").date()
req = HistoryRequest(rq_symbol1, exchange=Exchange.SHFE, start=start_time, end=end_time, interval=Interval.MINUTE)
print(req.symbol)
print(req.exchange)
print(req.start)
print(req.end)
data1 = rqdata_client.query_history(req)
print(data1)
#%%
data1 = DataFrame(data1)
print(data1)
#%%
rb2010_excel = pd.ExcelWriter('C:\\Users\\huangning\\Desktop\\期货自动化交易\\8-vnpy编程练习\\螺纹钢期货分钟数据.xlsx')  # 定义一个向Excel写入数据的对象
data1.to_excel(rb2010_excel, '20190901-20200901')  # 向该Excel中写入df1到Data1这个sheet
rb2010_excel.save()  # 保存Excel表格
rb2010_excel.close()  # 关闭Excel表格
# %%
