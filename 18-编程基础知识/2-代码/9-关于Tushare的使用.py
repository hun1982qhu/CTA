# 通过Tushare同时获得多只股票信息
# 因为Tushare的get命令目前只能一次获取一直股票的信息，为了同时获得多只股票的信息，需要构建一个函数，具体如下：

def multiple_stocks(tickers):
    def data(ticker):
        stocks = ts.get_k_data(ticker, start=‘2016-01-01', end='2017-07-01')
        stocks.set_index('date', inplace=True)
        # 原始数据中日期列里的数据形式上是日期，但并不是数据处理所需要的日期格式-因此需要将index列的日期转换成标准日期格式
        stocks.index = pd.to_datetime(stocks.index)
        return stocks
    datas = map(data, tickers)
    return pd.concat(datas, keys=tickers, names=['Tickers', 'Date'])


tickers = ['600030', '000001', '600426']
all_stocks = multiple_stocks(tickers)
print('通过函数运算同时获得多只股票信息：\n', all_stocks, '\n')

ts.bar('FG805', conn=cons, freq='D', asset='X', start_date='2017-11-01', end_date=‘')
