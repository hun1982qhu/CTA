# 股票收益的离散算法

Return离散 = (Pt - Pt-1 )/ Pt-1

# 股票收益的连续算法

Return连续 = ln(Pt / Pt-1)

# 第一种方法：用对数计算连续收益
hr_dk['return_continuous'] = np.log(hr_dk['close'] / hr_dk['close'].shift(1))  # 计算连续收益
# 第二种方法：列出收益百分比公式计算离散收益
hr_dk['return_discrete1'] = hr_dk['close'] / hr_dk['close'].shift(1) - 1 
# 第三种方法：使用pandas自带的pc_change命令直接计算收益百分比
hr_dk['return_discrete2'] = hr_dk[‘close'].pct_change() 
