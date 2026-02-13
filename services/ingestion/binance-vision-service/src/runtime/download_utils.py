"""下载工具（标准库实现，避免新增依赖）。

设计目标：
- 大文件流式下载（Vision ZIP 可能很大）
- 基础重试（网络抖动/临时失败）
- 404 可识别（用于“月度不存在则降级日度”的智能选择）
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import time
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DownloadResult:
    ok: bool
    status_code: Optional[int]
    error: Optional[str]


def download_file(url: str, dst: Path, *, timeout_seconds: float = 30.0, max_retries: int = 3) -> DownloadResult:
    dst.parent.mkdir(parents=True, exist_ok=True)

    tmp = dst.with_suffix(dst.suffix + ".part")
    if tmp.exists():
        try:
            tmp.unlink()
        except Exception:
            pass

    backoff = 1.0
    for attempt in range(max_retries):
        try:
            req = Request(url, headers={"User-Agent": "tradecat/binance-vision-service"})
            with urlopen(req, timeout=timeout_seconds) as resp:  # noqa: S310
                status = getattr(resp, "status", None)
                content_length = resp.getheader("Content-Length")
                expected_size = int(content_length) if content_length and content_length.isdigit() else None
                with tmp.open("wb") as f:
                    while True:
                        chunk = resp.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)

            if expected_size is not None:
                local_size = tmp.stat().st_size
                if local_size != expected_size:
                    raise OSError(f"下载大小不一致: local={local_size} expected={expected_size}")

            tmp.rename(dst)
            return DownloadResult(ok=True, status_code=status, error=None)
        except HTTPError as e:
            # 404 是结构性错误：上游确实没有这个文件，直接返回让上层降级。
            if int(getattr(e, "code", 0)) == 404:
                return DownloadResult(ok=False, status_code=404, error=str(e))
            logger.warning("下载失败（HTTP %s），重试中: %s (attempt=%d/%d)", e.code, url, attempt + 1, max_retries)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60.0)
        except (URLError, TimeoutError, OSError) as e:
            logger.warning("下载失败，重试中: %s (attempt=%d/%d)", e, attempt + 1, max_retries)
            time.sleep(backoff)
            backoff = min(backoff * 2, 60.0)

    return DownloadResult(ok=False, status_code=None, error="下载重试耗尽")


def probe_content_length(url: str, *, timeout_seconds: float = 30.0) -> int | None:
    """探测远端文件大小（字节）。

    优先 HEAD；若上游不支持 HEAD（405/501），降级 GET 读取响应头。
    返回 None 表示无法可靠获取大小（例如无 Content-Length）。
    """
    headers = {"User-Agent": "tradecat/binance-vision-service"}

    try:
        req = Request(url, method="HEAD", headers=headers)
        with urlopen(req, timeout=timeout_seconds) as resp:  # noqa: S310
            content_length = resp.getheader("Content-Length")
            if content_length and content_length.isdigit():
                return int(content_length)
            return None
    except HTTPError as e:
        if int(getattr(e, "code", 0)) not in {405, 501}:
            return None
    except Exception:
        return None

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout_seconds) as resp:  # noqa: S310
            content_length = resp.getheader("Content-Length")
            if content_length and content_length.isdigit():
                return int(content_length)
    except Exception:
        return None

    return None
