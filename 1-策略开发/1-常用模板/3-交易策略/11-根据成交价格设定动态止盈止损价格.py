def on_trade(self, trade: TradeData):
        """"""
        if self.pos != 0:
            if self.trade.direction == Direction.LONG:
                self.long_entry = trade.pirce
                self.long_tp = self.long_entry + self.fixed_tp
            else:
                self.short_entry = trade.pirce
                self.short_tp = self.short_entry - self.fixed_tp

        self.put_event()