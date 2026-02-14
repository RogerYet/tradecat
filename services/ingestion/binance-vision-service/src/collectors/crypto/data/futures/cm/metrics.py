"""Futures CM / metrics（Raw/基元：交易所指标，占位）

# 对齐官方目录语义
# - data/futures/cm/daily/metrics/{SYMBOL}/{SYMBOL}-metrics-YYYY-MM-DD.csv
#
# 落库目标（Raw/物理层）
# - crypto.raw_futures_cm_metrics
"""

from __future__ import annotations


def collect() -> None:
    raise NotImplementedError
