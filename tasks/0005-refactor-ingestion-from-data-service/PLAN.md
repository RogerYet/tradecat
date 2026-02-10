# PLAN - “拆分 + 迁移 + 对齐验证”的整套路径（说人话版）

## 1) 你要的“变化”是什么

从旧形态：

- 一个 data-service 目录里塞满 collectors/adapters，运行靠脚本 + sys.path hack

变成新形态：

- `tradecat/ingestion` 里拆成三类模块：
  - **providers**：拉取与标准化（WS/REST/ZIP）
  - **storage**：只管写库（COPY/upsert/幂等键）
  - **jobs**：编排（flush window、watermark、gap scan/backfill、retry/backoff）+ 观测

最终运行入口变成：`python -m tradecat.ingestion ...`（或等价 CLI），而不是 `python collectors/ws.py`。

## 2) 拆分映射（旧文件 → 新职责）

- `collectors/ws.py` → `jobs/candles_ws_1m.py` + `providers/binance/ws_cryptofeed.py` + `storage/timescale_writer.py`
- `collectors/backfill.py` → `jobs/backfill_gaps.py` + `providers/binance/vision_zip.py` + `providers/binance/rest_ccxt.py`
- `collectors/metrics.py` → `jobs/futures_metrics_5m.py` + `providers/binance/rest_fapi.py` + `storage/timescale_writer.py`
- `adapters/timescale.py` → `storage/timescale_writer.py`（保留 COPY+temp table 策略，保证性能）
- `adapters/ccxt.py` → `providers/binance/rest_ccxt.py`（符号加载/标准化也放这里）
- `adapters/rate_limiter.py` → `providers/_shared/rate_limit.py`（不跨层泄露）

## 3) 迁移节奏（安全、可回滚）

1) **先把新模块跑通，但不替换旧服务**
   - 新 ingestion 在 `/home/lenovo/tradecat/tradecat/ingestion/` 完成最小闭环
2) **并跑对齐**
   - 同时间窗跑旧实现与新实现，做 row-level 对齐验证
3) **再切换入口**
   - 生产/常用启动脚本再切到新 CLI（另立任务，避免混在本任务里）

## 4) 回滚协议

- 新 ingestion 失败：不影响旧 data-service（旧代码只读保留）
- 任何发现写入源仓库迹象：立即停止，修正运行根/环境变量/写入路径，再重新对齐

