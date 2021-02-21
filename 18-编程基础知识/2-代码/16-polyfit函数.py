polyfit(x, y, i) 用于计算回归方程， i代表自由度（阶数）
# 例：m = np.array([1, 2, 3, 4, 5])
n = m * 5 + 2
slope, intercept = np.polyfit(m, n, 1).round(2)
print(slope, intercept)
