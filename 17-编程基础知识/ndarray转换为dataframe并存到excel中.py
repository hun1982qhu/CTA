#%%
import numpy as np
import pandas as pd
#%%
x = np.array([[1, 2, 3], [4, 5, 6]])
# %%
y = np.array([[7, 8, 9]])
#%%
x = np.append(x, y, axis=0)
#%%
df = pd.DataFrame(x)
df.columns = ['a','b','c']
print(df)
# %%
rb888_excel = pd.ExcelWriter('D:\\期货自动化交易\\8-CTA_Development\\1-常用模板\\1-rqdata\\螺纹钢期货tick数据.xlsx')  # 定义一个向Excel写入数据的对象
df.to_excel(rb888_excel, "RB888tick数据")  # 向该Excel中写入df1到Data1这个sheet
rb888_excel.save()  # 保存Excel表格
rb888_excel.close()  # 关闭Excel表格
# %%
