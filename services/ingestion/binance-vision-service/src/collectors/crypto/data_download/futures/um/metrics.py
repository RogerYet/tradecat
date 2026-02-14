"""Futures UM / metrics（下载补齐，Raw/基元）

# 对齐官方目录语义
# - data/futures/um/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-YYYY-MM-DD.zip
# - data/futures/um/monthly/metrics/{SYMBOL}/{SYMBOL}-metrics-YYYY-MM.zip
#
# CSV 样本字段
# - 列：create_time,symbol,sum_open_interest,sum_open_interest_value,
#       count_toptrader_long_short_ratio,sum_toptrader_long_short_ratio,
#       count_long_short_ratio,sum_taker_long_short_vol_ratio
#
# 落库目标（Raw/物理层）
# - crypto.raw_futures_um_metrics
"""

from __future__ import annotations


def download_and_ingest() -> None:
    raise NotImplementedError
