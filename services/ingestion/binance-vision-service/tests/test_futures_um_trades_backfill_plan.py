from __future__ import annotations

from datetime import date, datetime, timezone

from src.collectors.crypto.data_download.futures.um.trades import (
    _build_plan,
    _date_range_ms_utc,
    _relpath_daily_zip,
    _relpath_monthly_zip,
)


def test_build_plan_full_month_prefers_monthly() -> None:
    plan = _build_plan("BTCUSDT", date(2024, 1, 1), date(2024, 1, 31), prefer_monthly=True)
    assert len(plan) == 1
    assert plan[0].kind == "monthly"
    assert plan[0].period == "2024-01"


def test_build_plan_full_month_daily_when_monthly_disabled() -> None:
    plan = _build_plan("BTCUSDT", date(2024, 1, 1), date(2024, 1, 31), prefer_monthly=False)
    assert len(plan) == 31
    assert {item.kind for item in plan} == {"daily"}
    assert plan[0].period == "2024-01-01"
    assert plan[-1].period == "2024-01-31"


def test_build_plan_mixed_partial_and_full_month() -> None:
    plan = _build_plan("BTCUSDT", date(2024, 1, 15), date(2024, 3, 10), prefer_monthly=True)
    monthly = [p for p in plan if p.kind == "monthly"]
    daily = [p for p in plan if p.kind == "daily"]
    assert len(monthly) == 1
    assert monthly[0].period == "2024-02"
    assert len(daily) == 27
    assert daily[0].period == "2024-01-15"
    assert daily[-1].period == "2024-03-10"


def test_date_range_ms_utc_end_is_exclusive_next_day() -> None:
    start_ms, end_ms = _date_range_ms_utc(date(2024, 2, 1), date(2024, 2, 1))
    expected_start = int(datetime(2024, 2, 1, tzinfo=timezone.utc).timestamp() * 1000)
    expected_end = int(datetime(2024, 2, 2, tzinfo=timezone.utc).timestamp() * 1000)
    assert start_ms == expected_start
    assert end_ms == expected_end


def test_relpath_templates_align_vision_download_layout() -> None:
    assert _relpath_daily_zip("BTCUSDT", date(2024, 2, 9)) == "data_download/futures/um/daily/trades/BTCUSDT/BTCUSDT-trades-2024-02-09.zip"
    assert _relpath_monthly_zip("BTCUSDT", "2024-02") == "data_download/futures/um/monthly/trades/BTCUSDT/BTCUSDT-trades-2024-02.zip"

