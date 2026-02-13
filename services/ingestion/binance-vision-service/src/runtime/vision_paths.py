"""Binance Vision 路径模板（严格对齐官方目录语义）。"""

from __future__ import annotations

from datetime import date


def relpath_futures_um_trades_daily(symbol: str, d: date) -> str:
    """官方相对路径：UM trades（日度 CSV）。

    例：
    - data/futures/um/daily/trades/BTCUSDT/BTCUSDT-trades-2026-02-09.csv
    """

    sym = symbol.upper()
    return f"data/futures/um/daily/trades/{sym}/{sym}-trades-{d:%Y-%m-%d}.csv"
