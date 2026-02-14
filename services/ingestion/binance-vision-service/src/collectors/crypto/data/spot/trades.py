"""Spot / trades（占位）

# 对齐官方目录语义
# - data/spot/daily/trades/{SYMBOL}/{SYMBOL}-trades-YYYY-MM-DD.csv
#
# 样本事实（来自 binance_vision_compass）
# - CSV 无 header
# - 列序：id, price, qty, quote_qty, time(us), is_buyer_maker, is_best_match
#
# 运行时参数（建议）
# - symbol: BTCUSDT
# - date: YYYY-MM-DD
#
# 输出
# - 本地落盘（严格对齐 Vision 路径）：data/spot/daily/trades/{SYMBOL}/{SYMBOL}-trades-{date}.csv
#
# 落库目标（Raw/物理层）
# - crypto.raw_spot_trades
"""

from __future__ import annotations


def collect() -> None:
    raise NotImplementedError
