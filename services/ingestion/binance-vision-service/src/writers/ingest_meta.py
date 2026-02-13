"""旁路元数据写入器（runs/watermark/gaps）。

目标：
- 不污染事实表（raw trades 只存事实）
- 仍能做到：可观测、可巡检、可补齐（你最关心 gap）
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Optional

import psycopg

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestRunSpec:
    exchange: str
    dataset: str
    mode: str  # realtime/backfill/repair


class IngestMetaWriter:
    def __init__(self, conn: psycopg.Connection):
        self._conn = conn

    def start_run(self, spec: IngestRunSpec) -> int:
        sql = """
        INSERT INTO crypto.ingest_runs (
          exchange, dataset, mode, status
        ) VALUES (
          %(exchange)s, %(dataset)s, %(mode)s, 'running'
        )
        RETURNING run_id
        """
        with self._conn.cursor() as cur:
            cur.execute(sql, {"exchange": spec.exchange, "dataset": spec.dataset, "mode": spec.mode})
            row = cur.fetchone()
            if not row:
                raise RuntimeError("无法创建 ingest_run")
            run_id = int(row[0])
        self._conn.commit()
        return run_id

    def finish_run(self, run_id: int, *, status: str, error_message: Optional[str] = None) -> None:
        sql = """
        UPDATE crypto.ingest_runs
        SET status = %(status)s,
            error_message = %(error_message)s,
            finished_at = NOW()
        WHERE run_id = %(run_id)s
        """
        with self._conn.cursor() as cur:
            cur.execute(sql, {"run_id": int(run_id), "status": status, "error_message": error_message})
        self._conn.commit()

    def upsert_watermark(self, *, exchange: str, dataset: str, symbol: str, last_time: int, last_id: int) -> None:
        sql = """
        INSERT INTO crypto.ingest_watermark (
          exchange, dataset, symbol, last_time, last_id
        ) VALUES (
          %(exchange)s, %(dataset)s, %(symbol)s, %(last_time)s, %(last_id)s
        )
        ON CONFLICT (exchange, dataset, symbol) DO UPDATE SET
          last_time = GREATEST(crypto.ingest_watermark.last_time, EXCLUDED.last_time),
          last_id   = GREATEST(crypto.ingest_watermark.last_id,   EXCLUDED.last_id),
          updated_at = NOW()
        """
        with self._conn.cursor() as cur:
            cur.execute(
                sql,
                {
                    "exchange": exchange,
                    "dataset": dataset,
                    "symbol": symbol.upper(),
                    "last_time": int(last_time),
                    "last_id": int(last_id),
                },
            )
        self._conn.commit()

    def insert_gap(
        self,
        *,
        exchange: str,
        dataset: str,
        symbol: str,
        start_time: int,
        end_time: int,
        reason: str,
        run_id: Optional[int],
    ) -> None:
        if start_time >= end_time:
            return

        sql = """
        INSERT INTO crypto.ingest_gaps (
          exchange, dataset, symbol, start_time, end_time, status, reason, run_id
        ) VALUES (
          %(exchange)s, %(dataset)s, %(symbol)s, %(start_time)s, %(end_time)s, 'open', %(reason)s, %(run_id)s
        )
        ON CONFLICT (exchange, dataset, symbol, start_time, end_time) DO NOTHING
        """
        with self._conn.cursor() as cur:
            cur.execute(
                sql,
                {
                    "exchange": exchange,
                    "dataset": dataset,
                    "symbol": symbol.upper(),
                    "start_time": int(start_time),
                    "end_time": int(end_time),
                    "reason": reason,
                    "run_id": int(run_id) if run_id is not None else None,
                },
            )
        self._conn.commit()

