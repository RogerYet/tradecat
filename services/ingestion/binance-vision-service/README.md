# binance-vision-service（Binance Vision Raw 对齐采集）

本服务用于：

- **实时**：用 `ccxtpro` WebSocket 拉取 Binance 数据，并落地为 **严格对齐** `data.binance.vision` 的目录结构与 CSV 字段；
- **历史回填**：用 Binance Vision `daily/monthly` ZIP 做全量补齐与最终对账（避免靠 REST 分页把历史拉穿）。

## 设计原则

- 每个 CSV 数据集对应一个“采集器卡片”（一个 Python 文件）
- 采集（extract）与落盘/落库（write）解耦：卡片只负责字段对齐；写入器负责幂等、文件命名与批量写入
- 只建/只写 `crypto.raw_*`（派生层 `crypto.agg_*` 暂不启用）

## 快速开始

```bash
cd services/ingestion/binance-vision-service
make install-dev

# 实时（UM trades）
BINANCE_VISION_DATABASE_URL=postgresql://... \
python3 -m src collect \
  --dataset crypto.data.futures.um.trades \
  --symbols BTCUSDT

# 历史回填（UM trades）
BINANCE_VISION_DATABASE_URL=postgresql://... \
BINANCE_DATA_BASE=https://data.binance.vision \
python3 -m src backfill \
  --dataset crypto.data_download.futures.um.trades \
  --symbols BTCUSDT \
  --start-date 2019-01-01 \
  --end-date 2026-02-01
```
