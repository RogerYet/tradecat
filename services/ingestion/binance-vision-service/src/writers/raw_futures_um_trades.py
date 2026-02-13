"""UM 合约逐笔（trades）Raw 入库写入器。

# 对齐目标
# - 表：crypto.raw_futures_um_trades
# - CSV 列：id,price,qty,quote_qty,time,is_buyer_maker
# - 关键约束：字段完备 + 幂等（ON CONFLICT DO NOTHING）
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import logging
from typing import Iterable, List

import psycopg

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RawFuturesUmTradeRow:
    exchange: str
    symbol: str
    id: int
    price: Decimal
    qty: Decimal
    quote_qty: Decimal
    time: int
    is_buyer_maker: bool


class RawFuturesUmTradesWriter:
    def __init__(self, conn: psycopg.Connection):
        self._conn = conn

    def insert_rows(self, rows: Iterable[RawFuturesUmTradeRow]) -> int:
        batch: List[RawFuturesUmTradeRow] = list(rows)
        if not batch:
            return 0

        sql = """
        INSERT INTO crypto.raw_futures_um_trades (
            exchange,
            symbol,
            id,
            price,
            qty,
            quote_qty,
            time,
            is_buyer_maker
        ) VALUES (
            %(exchange)s,
            %(symbol)s,
            %(id)s,
            %(price)s,
            %(qty)s,
            %(quote_qty)s,
            %(time)s,
            %(is_buyer_maker)s
        )
        ON CONFLICT (exchange, symbol, time, id) DO NOTHING
        """

        params = [
            {
                "exchange": r.exchange,
                "symbol": r.symbol,
                "id": r.id,
                "price": r.price,
                "qty": r.qty,
                "quote_qty": r.quote_qty,
                "time": r.time,
                "is_buyer_maker": r.is_buyer_maker,
            }
            for r in batch
        ]

        with self._conn.cursor() as cur:
            cur.executemany(sql, params)

        self._conn.commit()
        return len(batch)
