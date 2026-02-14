"""Futures CM / bookTicker（Raw/基元：买一卖一流，占位）

# 对齐官方目录语义
# - data/futures/cm/daily/bookTicker/{SYMBOL}/{SYMBOL}-bookTicker-YYYY-MM-DD.csv
#
# 落库目标（Raw/物理层）
# - crypto.raw_futures_cm_book_ticker
"""

from __future__ import annotations


def collect() -> None:
    raise NotImplementedError
