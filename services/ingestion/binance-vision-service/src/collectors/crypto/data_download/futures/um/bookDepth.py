"""Futures UM / bookDepth（下载补齐，Raw/基元）

# 对齐官方目录语义
# - data/futures/um/daily/bookDepth/{SYMBOL}/{SYMBOL}-bookDepth-YYYY-MM-DD.zip
# - data/futures/um/monthly/bookDepth/{SYMBOL}/{SYMBOL}-bookDepth-YYYY-MM.zip
#
# CSV 样本字段
# - 列：timestamp,percentage,depth,notional
#
# 落库目标（Raw/物理层）
# - crypto.raw_futures_um_book_depth
"""

from __future__ import annotations


def download_and_ingest() -> None:
    raise NotImplementedError
