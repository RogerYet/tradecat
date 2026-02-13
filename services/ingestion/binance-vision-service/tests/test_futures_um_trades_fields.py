from __future__ import annotations

from datetime import date
from decimal import Decimal

from src.collectors.crypto.data.futures.um.trades import (
    parse_um_trade_from_ccxt,
    um_trade_to_csv_row,
)
from src.runtime.decimal_utils import format_decimal_like_vision
from src.runtime.vision_paths import relpath_futures_um_trades_daily


def test_format_decimal_like_vision_trims_trailing_zeros_and_keeps_one_decimal() -> None:
    assert format_decimal_like_vision(Decimal("1125.0000")) == "1125.0"
    assert format_decimal_like_vision(Decimal("7028.00")) == "7028.0"
    assert format_decimal_like_vision(Decimal("492.0174")) == "492.0174"
    assert format_decimal_like_vision(Decimal("0")) == "0.0"


def test_relpath_futures_um_trades_daily() -> None:
    assert (
        relpath_futures_um_trades_daily("BTCUSDT", date(2026, 2, 9))
        == "data/futures/um/daily/trades/BTCUSDT/BTCUSDT-trades-2026-02-09.csv"
    )


def test_parse_um_trade_from_ccxt_and_csv_row_aligns_official_fields() -> None:
    trade = {
        "info": {
            "s": "BTCUSDT",
            "t": 7252042528,
            "p": "70280.0",
            "q": "0.1",
            "T": 1770595201730,
            "m": True,
        }
    }

    t = parse_um_trade_from_ccxt(trade, fallback_symbol="BTCUSDT")
    assert t.symbol == "BTCUSDT"
    assert t.id == 7252042528
    assert t.price == Decimal("70280.0")
    assert t.qty == Decimal("0.1")
    assert t.quote_qty == Decimal("7028.00")
    assert t.time == 1770595201730
    assert t.is_buyer_maker is True

    row = um_trade_to_csv_row(t)
    assert row[0] == "7252042528"  # id
    assert row[1] == "70280.0"  # price
    assert row[2] == "0.1"  # qty
    assert row[3] == "7028.0"  # quote_qty（至少 1 位小数）
    assert row[4] == "1770595201730"  # time
    assert row[5] == "true"  # is_buyer_maker
