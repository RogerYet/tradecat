"""Futures UM / metrics（Raw/基元：交易所指标）

# 对齐官方目录语义
# - data/futures/um/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-YYYY-MM-DD.csv
#
# 样本事实
# - CSV 有 header
# - 列：create_time,symbol,sum_open_interest,sum_open_interest_value,
#       count_toptrader_long_short_ratio,sum_toptrader_long_short_ratio,
#       count_long_short_ratio,sum_taker_long_short_vol_ratio
#
# 输出
# - data/futures/um/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-{date}.csv
#
# 落库目标（Raw/物理层）
# - crypto.raw_futures_um_metrics
"""

from __future__ import annotations


def collect() -> None:
    raise NotImplementedError
