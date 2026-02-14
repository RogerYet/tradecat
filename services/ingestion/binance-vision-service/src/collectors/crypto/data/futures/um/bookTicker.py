"""Futures UM / bookTicker（Raw/基元：买一卖一流）

# 对齐官方目录语义
# - data/futures/um/daily/bookTicker/{SYMBOL}/{SYMBOL}-bookTicker-YYYY-MM-DD.csv
#
# 样本事实
# - CSV 有 header
# - 列：update_id,best_bid_price,best_bid_qty,best_ask_price,best_ask_qty,transaction_time,event_time
#
# 输出
# - data/futures/um/daily/bookTicker/{SYMBOL}/{SYMBOL}-bookTicker-{date}.csv
#
# 落库目标（Raw/物理层）
# - crypto.raw_futures_um_book_ticker
"""

from __future__ import annotations


def collect() -> None:
    raise NotImplementedError
