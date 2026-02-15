"""binance-vision-service 入口。

当前阶段：以“采集器卡片（dataset card）”为单位逐个补齐。

# 运行示例

```bash
cd services/ingestion/binance-vision-service

# UM trades（实时，WS 优先）
DATABASE_URL=postgresql://... \
python3 -m src collect \
  --dataset crypto.data.futures.um.trades \
  --symbols BTCUSDT

# UM trades（历史回填，Binance Vision ZIP，按月/按日智能选择）
DATABASE_URL=postgresql://... \
BINANCE_DATA_BASE=https://data.binance.vision \
python3 -m src backfill \
  --dataset crypto.data_download.futures.um.trades \
  --symbols BTCUSDT \
  --start-date 2019-01-01 \
  --end-date 2026-02-01 \
  --no-files
```
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import date
import logging
from pathlib import Path

from src.config import load_config

logger = logging.getLogger(__name__)


def _parse_symbols(raw: str) -> list[str]:
    symbols = [s.strip().upper() for s in (raw or "").split(",") if s.strip()]
    if not symbols:
        raise ValueError("--symbols 不能为空")
    return symbols


def _parse_symbols_optional(raw: str) -> list[str] | None:
    symbols = [s.strip().upper() for s in (raw or "").split(",") if s.strip()]
    return symbols or None


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    parser = argparse.ArgumentParser(prog="binance-vision-service")
    parser.add_argument("--version", action="store_true", help="打印版本并退出")

    sub = parser.add_subparsers(dest="cmd")

    collect = sub.add_parser("collect", help="运行采集器卡片")
    collect.add_argument(
        "--dataset",
        required=True,
        choices=[
            # 逐步补齐（严格对齐 Vision 数据集）
            "crypto.data.futures.um.trades",
            "crypto.data.futures.cm.trades",
            "crypto.data.spot.trades",
        ],
        help="采集器卡片路径（与 src/collectors/crypto/data/** 镜像对应）",
    )
    collect.add_argument("--symbols", required=True, help="Binance Vision symbol 列表（逗号分隔），例如 BTCUSDT,ETHUSDT")
    collect.add_argument("--no-csv", action="store_true", help="不落盘 CSV（只入库）")
    collect.add_argument("--no-db", action="store_true", help="不入库（只落盘 CSV）")
    collect.add_argument("--flush-max-rows", type=int, default=2000, help="批量 flush 的最大行数")
    collect.add_argument("--flush-interval", type=float, default=1.0, help="批量 flush 的最大间隔（秒）")
    collect.add_argument("--window-seconds", type=int, default=300, help="近实时巡检窗口 W（秒），默认 300=5min")
    collect.add_argument("--rest-overlap-multiplier", type=int, default=3, help="REST 补拉 overlap = x*W，默认 x=3")
    collect.add_argument("--gap-threshold-seconds", type=int, default=30, help="超过该秒数未收到新成交则触发巡检补齐")
    collect.add_argument("--gap-check-interval", type=float, default=10.0, help="巡检循环间隔（秒）")

    backfill = sub.add_parser("backfill", help="运行下载回填卡片（Vision ZIP）")
    backfill.add_argument(
        "--dataset",
        required=True,
        choices=[
            "crypto.data_download.futures.um.trades",
            "crypto.data_download.futures.um.bookTicker",
            "crypto.data_download.futures.um.bookDepth",
            "crypto.data_download.futures.um.metrics",
            "crypto.data_download.futures.cm.trades",
            "crypto.data_download.spot.trades",
        ],
        help="下载回填卡片路径（与 src/collectors/crypto/data_download/** 镜像对应）",
    )
    backfill.add_argument("--symbols", required=True, help="Binance Vision symbol 列表（逗号分隔），例如 BTCUSDT")
    backfill.add_argument("--start-date", required=True, help="起始日期（UTC），例如 2019-01-01")
    backfill.add_argument("--end-date", required=True, help="结束日期（UTC），例如 2026-02-01")
    backfill.add_argument("--no-files", action="store_true", help="不落盘 ZIP/CSV（只入库）")
    backfill.add_argument("--no-db", action="store_true", help="不入库（只落盘 ZIP/CSV）")
    backfill.add_argument("--no-prefer-monthly", action="store_true", help="禁用月度 ZIP 优先（强制按日回填）")
    backfill.add_argument("--allow-no-checksum", action="store_true", help="允许缺失 CHECKSUM 时继续（会标记为 unverified）")

    repair = sub.add_parser("repair", help="运行缺口修复（消费 crypto.ingest_gaps）")
    repair.add_argument(
        "--dataset",
        required=True,
        choices=[
            "crypto.repair.futures.um.trades",
            "crypto.repair.futures.cm.trades",
            "crypto.repair.spot.trades",
        ],
        help="修复卡片路径（与 src/collectors/crypto/repair/** 镜像对应）",
    )
    repair.add_argument("--symbols", default="", help="只修复指定 symbols（逗号分隔）；为空表示不过滤（全部 open gaps）")
    repair.add_argument("--max-jobs", type=int, default=10, help="本次最多处理多少个 gap（默认 10）")
    repair.add_argument("--no-files", action="store_true", help="不落盘 ZIP（只入库）")
    repair.add_argument("--no-prefer-monthly", action="store_true", help="禁用月度 ZIP 优先（强制按日修复）")
    repair.add_argument("--allow-no-checksum", action="store_true", help="允许缺失 CHECKSUM 时继续（会标记为 unverified）")

    args = parser.parse_args()

    if args.version:
        logger.info("binance-vision-service v0.1.0")
        return

    if args.cmd not in {"collect", "backfill", "repair"}:
        logger.info(
            "服务骨架已就绪：请通过 `python3 -m src collect ...` / `python3 -m src backfill ...` / `python3 -m src repair ...` 运行采集器卡片。"
        )
        return

    cfg = load_config()
    service_root = Path(__file__).resolve().parent.parent

    symbols = _parse_symbols(args.symbols) if args.cmd in {"collect", "backfill"} else None

    if args.cmd == "collect":
        write_csv = not args.no_csv
        write_db = not args.no_db

        if args.dataset == "crypto.data.futures.um.trades":
            from src.collectors.crypto.data.futures.um.trades import collect_realtime

            asyncio.run(
                collect_realtime(
                    symbols=symbols,
                    service_root=service_root,
                    database_url=cfg.database_url,
                    write_csv=write_csv,
                    write_db=write_db,
                    flush_max_rows=int(args.flush_max_rows),
                    flush_interval_seconds=float(args.flush_interval),
                    window_seconds=int(args.window_seconds),
                    rest_overlap_multiplier=int(args.rest_overlap_multiplier),
                    gap_threshold_seconds=int(args.gap_threshold_seconds),
                    gap_check_interval_seconds=float(args.gap_check_interval),
                )
            )
            return

        if args.dataset == "crypto.data.futures.cm.trades":
            from src.collectors.crypto.data.futures.cm.trades import collect_realtime

            asyncio.run(
                collect_realtime(
                    symbols=symbols,
                    service_root=service_root,
                    database_url=cfg.database_url,
                    write_csv=write_csv,
                    write_db=write_db,
                    flush_max_rows=int(args.flush_max_rows),
                    flush_interval_seconds=float(args.flush_interval),
                    window_seconds=int(args.window_seconds),
                    rest_overlap_multiplier=int(args.rest_overlap_multiplier),
                    gap_threshold_seconds=int(args.gap_threshold_seconds),
                    gap_check_interval_seconds=float(args.gap_check_interval),
                )
            )
            return

        if args.dataset == "crypto.data.spot.trades":
            from src.collectors.crypto.data.spot.trades import collect_realtime

            asyncio.run(
                collect_realtime(
                    symbols=symbols,
                    service_root=service_root,
                    database_url=cfg.database_url,
                    write_csv=write_csv,
                    write_db=write_db,
                    flush_max_rows=int(args.flush_max_rows),
                    flush_interval_seconds=float(args.flush_interval),
                    window_seconds=int(args.window_seconds),
                    rest_overlap_multiplier=int(args.rest_overlap_multiplier),
                    gap_threshold_seconds=int(args.gap_threshold_seconds),
                    gap_check_interval_seconds=float(args.gap_check_interval),
                )
            )
            return

        raise RuntimeError(f"未知 dataset: {args.dataset}")

    if args.cmd == "backfill":
        write_files = not args.no_files
        write_db = not args.no_db

        try:
            start_date = date.fromisoformat(str(args.start_date))
            end_date = date.fromisoformat(str(args.end_date))
        except ValueError as e:
            raise ValueError("start-date/end-date 格式必须是 YYYY-MM-DD") from e

        if args.dataset == "crypto.data_download.futures.um.trades":
            from src.collectors.crypto.data_download.futures.um.trades import download_and_ingest

            download_and_ingest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                service_root=service_root,
                database_url=cfg.database_url,
                binance_data_base=cfg.binance_data_base,
                write_files=write_files,
                write_db=write_db,
                prefer_monthly=not bool(args.no_prefer_monthly),
                allow_no_checksum=bool(args.allow_no_checksum),
            )
            return

        if args.dataset == "crypto.data_download.futures.um.bookTicker":
            from src.collectors.crypto.data_download.futures.um.bookTicker import download_and_ingest

            download_and_ingest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                service_root=service_root,
                database_url=cfg.database_url,
                binance_data_base=cfg.binance_data_base,
                write_files=write_files,
                write_db=write_db,
                prefer_monthly=not bool(args.no_prefer_monthly),
                allow_no_checksum=bool(args.allow_no_checksum),
            )
            return

        if args.dataset == "crypto.data_download.futures.um.bookDepth":
            from src.collectors.crypto.data_download.futures.um.bookDepth import download_and_ingest

            download_and_ingest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                service_root=service_root,
                database_url=cfg.database_url,
                binance_data_base=cfg.binance_data_base,
                write_files=write_files,
                write_db=write_db,
                prefer_monthly=not bool(args.no_prefer_monthly),
                allow_no_checksum=bool(args.allow_no_checksum),
            )
            return

        if args.dataset == "crypto.data_download.futures.um.metrics":
            from src.collectors.crypto.data_download.futures.um.metrics import download_and_ingest

            download_and_ingest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                service_root=service_root,
                database_url=cfg.database_url,
                binance_data_base=cfg.binance_data_base,
                write_files=write_files,
                write_db=write_db,
                prefer_monthly=not bool(args.no_prefer_monthly),
                allow_no_checksum=bool(args.allow_no_checksum),
            )
            return

        if args.dataset == "crypto.data_download.futures.cm.trades":
            from src.collectors.crypto.data_download.futures.cm.trades import download_and_ingest

            download_and_ingest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                service_root=service_root,
                database_url=cfg.database_url,
                binance_data_base=cfg.binance_data_base,
                write_files=write_files,
                write_db=write_db,
                prefer_monthly=not bool(args.no_prefer_monthly),
                allow_no_checksum=bool(args.allow_no_checksum),
            )
            return

        if args.dataset == "crypto.data_download.spot.trades":
            from src.collectors.crypto.data_download.spot.trades import download_and_ingest

            download_and_ingest(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                service_root=service_root,
                database_url=cfg.database_url,
                binance_data_base=cfg.binance_data_base,
                write_files=write_files,
                write_db=write_db,
                prefer_monthly=not bool(args.no_prefer_monthly),
                allow_no_checksum=bool(args.allow_no_checksum),
            )
            return

        raise RuntimeError(f"未知 dataset: {args.dataset}")

    if args.cmd == "repair":
        write_files = not args.no_files
        symbols = _parse_symbols_optional(args.symbols)

        if args.dataset == "crypto.repair.futures.um.trades":
            from src.collectors.crypto.repair.futures.um.trades import repair_open_gaps

            r = repair_open_gaps(
                service_root=service_root,
                database_url=cfg.database_url,
                binance_data_base=cfg.binance_data_base,
                symbols=symbols,
                max_jobs=int(args.max_jobs),
                write_files=write_files,
                prefer_monthly=not bool(args.no_prefer_monthly),
                allow_no_checksum=bool(args.allow_no_checksum),
            )
            logger.info("repair 完成: claimed=%d closed=%d reopened=%d", r.claimed, r.closed, r.reopened)
            return

        if args.dataset == "crypto.repair.futures.cm.trades":
            from src.collectors.crypto.repair.futures.cm.trades import repair_open_gaps

            r = repair_open_gaps(
                service_root=service_root,
                database_url=cfg.database_url,
                binance_data_base=cfg.binance_data_base,
                symbols=symbols,
                max_jobs=int(args.max_jobs),
                write_files=write_files,
                prefer_monthly=not bool(args.no_prefer_monthly),
                allow_no_checksum=bool(args.allow_no_checksum),
            )
            logger.info("repair 完成: claimed=%d closed=%d reopened=%d", r.claimed, r.closed, r.reopened)
            return

        if args.dataset == "crypto.repair.spot.trades":
            from src.collectors.crypto.repair.spot.trades import repair_open_gaps

            r = repair_open_gaps(
                service_root=service_root,
                database_url=cfg.database_url,
                binance_data_base=cfg.binance_data_base,
                symbols=symbols,
                max_jobs=int(args.max_jobs),
                write_files=write_files,
                prefer_monthly=not bool(args.no_prefer_monthly),
                allow_no_checksum=bool(args.allow_no_checksum),
            )
            logger.info("repair 完成: claimed=%d closed=%d reopened=%d", r.claimed, r.closed, r.reopened)
            return

        raise RuntimeError(f"未知 dataset: {args.dataset}")

    logger.info("请通过 `python3 -m src collect ...` / `python3 -m src backfill ...` / `python3 -m src repair ...` 运行采集器卡片。")
    return


if __name__ == "__main__":
    main()
