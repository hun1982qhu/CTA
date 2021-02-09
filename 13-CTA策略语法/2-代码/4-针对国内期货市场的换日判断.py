 # 针对国内期货市场的换日判断
    if self.last_bar.time < time(16, 0) and bar.date.time > time(16, 0):
        pass