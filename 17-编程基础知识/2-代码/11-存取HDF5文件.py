四、存取HDF5文件命令
把数据存入HDF5文件
# 生成数据
profit_data = ts.get_profit_data(2020, 1)
# 将生成的数据转化成想要构建的数据结构，例如DataFrame
data = pd.DataFrame(profit_data) 
# 选定路径，在选定路径下确定文件名，文件名后缀为h5，打开方式为w（只写模式）
hdf = pd.HDFStore('/Users/huangning/PycharmProjects/untitled/data/2020年1季度利润表.h5', ‘w')
# 打开新创建的hdf5文件
hdf.open()
# 将生成的数据存入hdf5文件
hdf['data'] = profit_data
# 一定要记得关闭打开的hdf5文件
hdf.close()

从HDF5文件中读取数据
# 打开文件：路径+文件名+读取方式（一般为只读方式r）
hdf = pd.HDFStore('/Users/huangning/PycharmProjects/untitled/data/2020年1季度利润表.h5', ‘r')
# 从打开的文件中读取数据
profit_data = hdf6[‘data']
# 输出符合条件的数据
print(profit_data1[profit_data1['roe'] > 15].head())
print('条件筛选结果：\n', profit_data1[(profit_data1['roe'] > 15) & (profit_data1['net_profit_ratio'] > 20)], '\n')
hdf6.close()
