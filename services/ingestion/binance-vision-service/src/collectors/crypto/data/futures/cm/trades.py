"""Futures CM / trades（Raw/基元：逐笔成交，占位）

# 对齐官方目录语义
# - data/futures/cm/daily/trades/{SYMBOL}/{SYMBOL}-trades-YYYY-MM-DD.csv
#
# 落库目标（Raw/物理层）
# - crypto.raw_futures_cm_trades
"""

from __future__ import annotations


def collect() -> None:
    raise NotImplementedError
