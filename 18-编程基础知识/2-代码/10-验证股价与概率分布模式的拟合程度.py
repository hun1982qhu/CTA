# 用stats.probplot命令验证股价与某种概率分布模式（如正态分布）的拟合程度
zxzq = price_change['600030']

fig = plt.figure(figsize=(7, 5))
ax = fig.add_subplot(111)
stats.probplot(zxzq, dist='norm', plot=ax)  
plt.show()

