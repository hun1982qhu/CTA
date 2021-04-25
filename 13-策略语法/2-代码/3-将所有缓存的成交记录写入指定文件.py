# 将所有缓存的成交记录写入指定文件
    def on_stop(self):
        self.write_log("策略停止")

        with open("trade_result.txt") as f:
            for trade in self.trades:
                f.write(str(trade))