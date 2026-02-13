from __future__ import annotations

from pathlib import Path
import zipfile

import src.collectors.crypto.data_download.futures.um.trades as um_trades_download
from src.runtime.download_utils import DownloadResult


def _write_zip_with_csv(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("sample.csv", content)


def test_download_or_repair_keeps_existing_zip_when_remote_size_matches(tmp_path: Path, monkeypatch) -> None:
    dst = tmp_path / "BTCUSDT-trades-2026-02.zip"
    _write_zip_with_csv(dst, "id,price,qty,quote_qty,time,is_buyer_maker\n1,1.0,1.0,1.0,1,true\n")

    monkeypatch.setattr(um_trades_download, "probe_content_length", lambda *args, **kwargs: dst.stat().st_size)

    def _should_not_download(*args, **kwargs) -> DownloadResult:
        raise AssertionError("remote size 一致时不应触发重下")

    monkeypatch.setattr(um_trades_download, "download_file", _should_not_download)

    result = um_trades_download._download_or_repair_zip("https://example.com/a.zip", dst)
    assert result.ok is True
    assert um_trades_download._zip_has_csv(dst)


def test_download_or_repair_redownloads_when_remote_size_mismatch(tmp_path: Path, monkeypatch) -> None:
    dst = tmp_path / "BTCUSDT-trades-2026-03.zip"
    _write_zip_with_csv(dst, "id,price,qty,quote_qty,time,is_buyer_maker\n1,1.0,1.0,1.0,1,true\n")

    monkeypatch.setattr(um_trades_download, "probe_content_length", lambda *args, **kwargs: dst.stat().st_size + 10)

    called = {"value": False}

    def _fake_download(url: str, target: Path, *, timeout_seconds: float = 30.0, max_retries: int = 3) -> DownloadResult:
        called["value"] = True
        _write_zip_with_csv(target, "id,price,qty,quote_qty,time,is_buyer_maker\n2,2.0,2.0,4.0,2,false\n")
        return DownloadResult(ok=True, status_code=200, error=None)

    monkeypatch.setattr(um_trades_download, "download_file", _fake_download)

    result = um_trades_download._download_or_repair_zip("https://example.com/b.zip", dst)
    assert called["value"] is True
    assert result.ok is True
    assert um_trades_download._zip_has_csv(dst)
