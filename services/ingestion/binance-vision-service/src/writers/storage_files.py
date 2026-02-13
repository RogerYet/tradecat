"""storage.files 写入器（获取/创建 file_id）。

# 设计目标
# - 任何一行事实数据必须可回溯到官方相对路径 rel_path
# - rel_path 唯一，因此我们可以通过 upsert 得到稳定的 file_id
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import logging
from typing import Dict, Optional

import psycopg

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StorageFileSpec:
    rel_path: str
    source: str
    market_root: str
    market: Optional[str]
    product: Optional[str]
    frequency: Optional[str]
    dataset: Optional[str]
    symbol: Optional[str]
    interval: Optional[str]
    file_date: Optional[date]
    file_month: Optional[date]
    content_kind: str = "csv"


class StorageFilesWriter:
    """storage.files 的最小 upsert 封装（带内存缓存）。"""

    def __init__(self, conn: psycopg.Connection):
        self._conn = conn
        self._cache: Dict[str, int] = {}

    def get_or_create_file_id(self, spec: StorageFileSpec) -> int:
        if spec.rel_path in self._cache:
            return self._cache[spec.rel_path]

        sql = """
        INSERT INTO storage.files (
            rel_path,
            content_kind,
            source,
            market_root,
            market,
            product,
            frequency,
            dataset,
            symbol,
            interval,
            file_date,
            file_month
        ) VALUES (
            %(rel_path)s,
            %(content_kind)s,
            %(source)s,
            %(market_root)s,
            %(market)s,
            %(product)s,
            %(frequency)s,
            %(dataset)s,
            %(symbol)s,
            %(interval)s,
            %(file_date)s,
            %(file_month)s
        )
        ON CONFLICT (rel_path)
        DO UPDATE SET rel_path = EXCLUDED.rel_path
        RETURNING file_id
        """

        with self._conn.cursor() as cur:
            cur.execute(
                sql,
                {
                    "rel_path": spec.rel_path,
                    "content_kind": spec.content_kind,
                    "source": spec.source,
                    "market_root": spec.market_root,
                    "market": spec.market,
                    "product": spec.product,
                    "frequency": spec.frequency,
                    "dataset": spec.dataset,
                    "symbol": spec.symbol,
                    "interval": spec.interval,
                    "file_date": spec.file_date,
                    "file_month": spec.file_month,
                },
            )
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"无法获取 file_id: {spec.rel_path}")
            file_id = int(row[0])

        self._conn.commit()
        self._cache[spec.rel_path] = file_id
        return file_id
