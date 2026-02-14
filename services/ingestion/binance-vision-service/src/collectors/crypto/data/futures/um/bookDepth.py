"""Futures UM / bookDepth（Raw/基元：百分比档位深度曲线）

# 对齐官方目录语义
# - data/futures/um/daily/bookDepth/{SYMBOL}/{SYMBOL}-bookDepth-YYYY-MM-DD.csv
#
# 样本事实
# - CSV 有 header
# - 列：timestamp,percentage,depth,notional
#
# 输出
# - data/futures/um/daily/bookDepth/{SYMBOL}/{SYMBOL}-bookDepth-{date}.csv
#
# 落库目标（Raw/物理层）
# - crypto.raw_futures_um_book_depth
"""

from __future__ import annotations


def collect() -> None:
    raise NotImplementedError
