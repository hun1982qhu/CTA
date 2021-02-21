# iterrows()
iter就是iterate 即迭代的意思
e.g. :
import numpy as np
import pandas as pd

df = pd.DataFrame(np.random.randn(4, 2))
df.columns = ['A', 'B']
df.index = ['a', 'b', 'c', 'd']
print(df)

df.iterrows()
for i in df.iterrows():
    print(i)
    print(i[1]['B'])
    print(type(i[1]))
# 理解iterrows()函数的关键就是：
# pd.iterrows()生成的是一个生成器对象
# 将变量赋值放入这个对象生成的由这个对象得到的是一个元组，元组的key是pd的index，值是一个series
