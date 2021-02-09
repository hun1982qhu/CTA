# 用python作图，不能显示中文标题，则添加以下代码（适用mac）
mpl.rcParams['font.sans-serif'] = ['Arial Unicode MS']
mpl.rcParams['axes.unicode_minus'] = False

plt.axhline(threshold, color=‘r’)

十七、关于作图
多个子图显示，不显示横坐标轴
例如：

plt.gca().axes.get_xaxis().set_visible(False)  # 不显示横坐标轴

设置图例位置

使用loc参数

plt.legend(loc='lower left')

0: ‘best'

1: ‘upper right'

2: ‘upper left'

3: ‘lower left'

4: ‘lower right'

5: ‘right'

6: ‘center left'

7: ‘center right'

8: ‘lower center'

9: ‘upper center'

10: ‘center'
