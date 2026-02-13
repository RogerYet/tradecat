"""时间工具。

# 设计约束
# - Binance Vision 的 trades 时间戳为 epoch(ms)；spot 为 epoch(us)
# - 我们必须避免 float 引入的时间舍入误差（模型训练/回测对齐需要稳定可复现）
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone


def ms_to_datetime_utc(epoch_ms: int) -> datetime:
    """epoch(ms) -> UTC aware datetime（无 float 误差）。"""
    seconds, ms = divmod(int(epoch_ms), 1000)
    return datetime.fromtimestamp(seconds, tz=timezone.utc) + timedelta(milliseconds=ms)


def ms_to_date_utc(epoch_ms: int) -> date:
    """epoch(ms) -> UTC date。"""
    return ms_to_datetime_utc(epoch_ms).date()
