# 发邮件
    def on_trade(self, trade: TradeData):
        msg = f"新的成交，策略{self.strategy_name}，方向{trade.direction}，开平{trade.offset}，当前仓位{self.pos}"
        self.send_email(msg)