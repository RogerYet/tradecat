"""Futures UM / bookTicker（下载补齐，Raw/基元）

# 对齐官方目录语义
# - data/futures/um/daily/bookTicker/{SYMBOL}/{SYMBOL}-bookTicker-YYYY-MM-DD.zip
# - data/futures/um/monthly/bookTicker/{SYMBOL}/{SYMBOL}-bookTicker-YYYY-MM.zip
#
# CSV 样本字段
# - 列：update_id,best_bid_price,best_bid_qty,best_ask_price,best_ask_qty,transaction_time,event_time
#
# 落库目标（Raw/物理层）
# - crypto.raw_futures_um_book_ticker
"""

from __future__ import annotations


def download_and_ingest() -> None:
    raise NotImplementedError
