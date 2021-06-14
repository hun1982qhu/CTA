from copy import copy
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime

import numpy as np

from vnpy.trader.constant import Direction, Offset
from vnpy.trader.object import BarData


@dataclass
class PnlOrderData:
    """虚拟委托数据"""
    direction: Direction
    offset: Offset
    price: float
    volume: float


@dataclass
class PnlTradeData:
    """虚拟成交数据"""
    datetime: datetime
    direction: Direction
    offset: Offset
    price: float
    volume: float


class PnlTracker:
    """"""

    def __init__(self, size: int, balance: int = 0):
        """"""
        self._pos: int = 0                          # 当前持仓
        self._size: int = size                      # 合约乘数
        self._balance: int = balance                # 当前的累计净值
        self._last_bar: BarData = None              # 上一根K线对象
        self._balances: Dict[datetime, float] = {}  # 净值记录
        self._pnls: Dict[datetime, float] = {}      # 盈亏记录
        self._orders: List[PnlOrderData] = []       # 委托记录（活动状态）
        self._trades: List[PnlTradeData] = []       # 成交记录

    def _send_order(
        self, direction: Direction, offset: Offset, price: float, volume: float
    ) -> None:
        """
        缓存限价委托信息
        """
        order = PnlOrderData(direction, offset, price, volume)
        self._orders.append(order)

    def buy(self, price: float, volume: float) -> None:
        """买开"""
        self._send_order(Direction.LONG, Offset.OPEN, price, volume)

    def sell(self, price: float, volume: float) -> None:
        """卖平"""
        self._send_order(Direction.SHORT, Offset.CLOSE, price, volume)

    def short(self, price: float, volume: float) -> None:
        """卖开"""
        self._send_order(Direction.SHORT, Offset.OPEN, price, volume)

    def cover(self, price: float, volume: float) -> None:
        """买平"""
        self._send_order(Direction.LONG, Offset.CLOSE, price, volume)

    def cancel_all(self) -> None:
        """全撤"""
        self._orders.clear()

    def on_bar(self, bar: BarData) -> None:
        """
        K线更新，驱动虚拟委托撮合以及虚拟盈亏计算逻辑。
        """
        # 首先要记录第一根K线收盘价，否则无法计算
        if not self._last_bar:
            self._last_bar = bar
            return

        # 计算盈亏
        holding_pnl = self._calculate_holding_pnl(bar)
        trading_pnl = self._calculate_trading_pnl(bar)

        total_pnl = holding_pnl + trading_pnl
        self._pnls[bar.datetime] = total_pnl

        # 更新累计净值
        self._balance += total_pnl
        self._balances[bar.datetime] = self._balance

        # 保存上一根K线
        self._last_bar = bar

    def _calculate_holding_pnl(self, bar: BarData) -> float:
        """计算持仓盈亏"""
        change = bar.close_price - self._last_bar.close_price
        holding_pnl = change * self._size * self._pos
        return holding_pnl

    def _calculate_trading_pnl(self, bar: BarData) -> float:
        """计算交易盈亏"""
        trading_pnl = 0

        orders = copy(self._orders)
        for order in orders:
            pos_change = 0

            # 买入委托，且K线最低价低于买入限价，则成交
            if (order.direction == Direction.LONG
                    and bar.low_price <= order.price):
                # 成交价格是限价和K线开盘价中的最大值
                trade_price = max(order.price, bar.open_price)
                pos_change = order.volume
            # 卖出则相反
            elif (order.direction == Direction.SHORT
                  and bar.high_price >= order.price):
                trade_price = min(order.price, bar.open_price)
                pos_change = -order.volume

            if pos_change:
                # 更新持仓
                self._pos += pos_change

                # 计算该笔成交到K线收盘的盈亏
                trade_pnl = (bar.close_price - trade_price) * \
                    self._size * pos_change

                # 累加到这根K线的交易盈亏上
                trading_pnl += trade_pnl

                # 从列表中移除已成交的该笔委托
                self._orders.remove(order)

                # 记录成交数据
                trade = PnlTradeData(
                    datetime=bar.datetime,
                    direction=order.direction,
                    offset=order.offset,
                    price=trade_price,
                    volume=order.volume
                )
                self._trades.append(trade)

        return trading_pnl

    def get_pnl_array(self, count: int):
        """获取长度为count的历史盈亏序列"""
        pnls = list(self._pnls.values())
        if len(pnls) < count:
            return None

        array = np.array(pnls[-count:])
        return array

    def get_last_pnl(self):
        """获取最新的盈亏数据"""
        pnls = list(self._pnls.values())
        return pnls[-1]

    def get_last_dt(self):
        """获取最新的盈亏日期"""
        dts = list(self._pnls.keys())
        return dts[-1]

    def get_balance_array(self, count: int):
        """获取长度为count的历史净值序列"""
        balances = list(self._balances.values())
        if len(balances) < count:
            return None

        array = np.array(balances[-count:])
        return array

    def get_last_balance(self):
        """获取最新的净值数据"""
        return self._balance

    def get_all_trades(self):
        """获取所有虚拟成交记录"""
        return copy(self._trades)
