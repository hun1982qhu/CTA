# 缓存3根K线，用于判断高低点的拐点
self.bar_list.append(bar)
if len(self.bar_list) <= 3:
    return
elif len(self.bar_list) > 3:
    self.bar_list.pop(0)

last_bar1 = self.bar_list[-2]
last_bar2 = self.bar_list[-3]