二、用python作图，不能显示中文标题，则添加以下代码（适用mac）
mpl.rcParams['font.sans-serif'] = ['Arial Unicode MS']
mpl.rcParams['axes.unicode_minus'] = False
