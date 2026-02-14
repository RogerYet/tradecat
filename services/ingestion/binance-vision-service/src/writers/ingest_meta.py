"""旁路元数据写入器（runs/watermark/gaps）。

目标：
- 不污染事实表（raw trades 只存事实）
- 仍能做到：可观测、可巡检、可补齐（你最关心 gap）
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Optional, Sequence

import psycopg

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestRunSpec:
    exchange: str
    dataset: str
    mode: str  # realtime/backfill/repair


@dataclass(frozen=True)
class IngestGap:
    gap_id: int
    exchange: str
    dataset: str
    symbol: str
    start_time: int
    end_time: int
    reason: Optional[str]
    status: str
    run_id: Optional[int]


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

    def claim_open_gaps(
        self,
        *,
        exchange: str,
        dataset: str,
        symbols: Optional[Sequence[str]],
        limit: int,
        run_id: int,
    ) -> list[IngestGap]:
        """认领 open gaps（open -> repairing），用于 repair worker 的并发安全消费。

        说明：
        - 使用 `FOR UPDATE SKIP LOCKED`，允许多个 repair 进程并行工作但不重复处理同一 gap。
        - 认领后会写入 `run_id`（指向本次 repair ingest_run）。
        """
        symbols_norm = [str(s).upper() for s in (symbols or []) if str(s).strip()]

        sql = """
        WITH picked AS (
          SELECT gap_id
          FROM crypto.ingest_gaps
          WHERE exchange = %(exchange)s
            AND dataset = %(dataset)s
            AND status = 'open'
            AND (%(symbols_any)s = FALSE OR symbol = ANY(%(symbols)s::text[]))
          ORDER BY detected_at ASC
          FOR UPDATE SKIP LOCKED
          LIMIT %(limit)s
        )
        UPDATE crypto.ingest_gaps g
        SET status = 'repairing',
            run_id = %(run_id)s
        FROM picked
        WHERE g.gap_id = picked.gap_id
        RETURNING g.gap_id, g.exchange, g.dataset, g.symbol, g.start_time, g.end_time, g.reason, g.status, g.run_id
        """

        with self._conn.cursor() as cur:
            cur.execute(
                sql,
                {
                    "exchange": exchange,
                    "dataset": dataset,
                    "symbols_any": bool(symbols_norm),
                    "symbols": symbols_norm,
                    "limit": int(limit),
                    "run_id": int(run_id),
                },
            )
            rows = cur.fetchall() or []
        self._conn.commit()
        return [
            IngestGap(
                gap_id=int(r[0]),
                exchange=str(r[1]),
                dataset=str(r[2]),
                symbol=str(r[3]),
                start_time=int(r[4]),
                end_time=int(r[5]),
                reason=str(r[6]) if r[6] is not None else None,
                status=str(r[7]),
                run_id=int(r[8]) if r[8] is not None else None,
            )
            for r in rows
        ]

    def close_gap(self, gap_id: int) -> None:
        self._set_gap_status(gap_id, status="closed", reason=None)

    def reopen_gap(self, gap_id: int, *, reason: Optional[str] = None) -> None:
        self._set_gap_status(gap_id, status="open", reason=reason)

    def ignore_gap(self, gap_id: int, *, reason: Optional[str] = None) -> None:
        self._set_gap_status(gap_id, status="ignored", reason=reason)

    def _set_gap_status(self, gap_id: int, *, status: str, reason: Optional[str]) -> None:
        sql = """
        UPDATE crypto.ingest_gaps
        SET status = %(status)s,
            reason = COALESCE(%(reason)s, crypto.ingest_gaps.reason)
        WHERE gap_id = %(gap_id)s
        """
        with self._conn.cursor() as cur:
            cur.execute(sql, {"gap_id": int(gap_id), "status": status, "reason": reason})
        self._conn.commit()
