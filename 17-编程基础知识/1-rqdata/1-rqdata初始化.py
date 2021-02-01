#%%
import rqdatac as rq 
from rqdatac import * 
rq.init('13581903798','hun829248')
import talib
import pandas as pd
import numpy as np
#%%
data = get_price("RB2010", start_date="2020-01-02", end_date="2020-01-03", frequency="tick")
#%%
# rb888_excel = pd.ExcelWriter('D:\\期货自动化交易\\8-CTA_Development\\1-常用模板\\1-rqdata\\螺纹钢期货tick数据.xlsx')  # 定义一个向Excel写入数据的对象
# data.to_excel(rb888_excel, "RB888tick数据")  # 向该Excel中写入df1到Data1这个sheet
# rb888_excel.save()  # 保存Excel表格
# rb888_excel.close()  # 关闭Excel表格
#%%
print(data)
#%%
data['cci'] = talib.CCI(data['high'], data['low'], data['close'], timeperiod=14)
print("cci值为:", data['cci'])
data1 = np.array(data['cci'])
print("data1：", data1)
print("data1[-1]:", data1[-1])
print("data1[-2]:", data1[-2])
print("data1[-3]:", data1[-3])

a = data1[-1]
b = data1[-2]
c = data1[-3]

print(data1[-1] < 100)
# %%
