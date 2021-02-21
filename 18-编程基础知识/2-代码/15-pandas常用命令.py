data.index = pd.to_datetime(data.index)
hs300[‘return'] = np.log(hs300['price'] / hs300['price'].shift(1))
rolling()
cumsum cumprod
dropna() drop也可以用于删除DataFrame中某行、某列
bfill()    ffill()   
fillna()

data[['open', ‘close']].max(axis=1)  
data[['open', ‘close']].min(axis=1)

data[['open', ‘close’]].all(axis=1) 要满足所有条件
data[['open', ‘close’]].any(axis=1) 只要满足其中一个条件

data[‘debt'].astype(np.float64)
