# STATUS - 进度真相源

## State

- Status: In Progress
- Updated: 2026-02-14

## Live Evidence（规划阶段已观察到的事实）

> 说明：以下为规划阶段在仓库内执行的“只读检查”所得证据片段，用于锁定现状与后续 diff 的参照点。

### Evidence 1: tasks 索引现状与新任务编号

- Command: `ls -la tasks && sed -n '1,40p' tasks/INDEX.md`
- Observed (excerpt):
  - 已存在任务：`0001` ~ `0005`
  - INDEX.md 最大编号：`0005` → 本任务编号选择：`0006`

### Evidence 2: 下载工具没有 checksum 逻辑

- Source: `services/ingestion/binance-vision-service/src/runtime/download_utils.py:29-73`
- Observed (excerpt):
  - 仅校验 `Content-Length`（若存在）与本地大小一致
  - 未出现 `CHECKSUM/sha256` 相关代码路径

### Evidence 3: UM 回填下载修复仅依赖 size 与 zip 可打开

- Source: `services/ingestion/binance-vision-service/src/collectors/crypto/data_download/futures/um/trades.py:167-196`
- Observed (excerpt):
  - `probe_content_length` + `_zip_has_csv` 决定是否重下
  - 未做 sha256 校验

### Evidence 4: 实时侧会写 ingest_gaps（但无 repair 消费者）

- Source: `services/ingestion/binance-vision-service/src/collectors/crypto/data/futures/um/trades.py:322-360`
- Observed (excerpt):
  - stale 触发 `insert_gap(...)`
  - 仅 REST overlap 补拉，缺口无“闭环关闭”逻辑

## Next Action（执行 Agent 的首个 P0）

- 继续完成 P0：让 repair 闭环落地，并在真实库里验证 `open -> repairing -> closed` 的状态迁移与对账口径。

## Execution Evidence（已落地的变更与验证）

### Evidence 5: `.CHECKSUM` 格式确认 + 本地 SHA256 对齐

- Command: `curl -sSfL "https://data.binance.vision/data/futures/um/daily/trades/BTCUSDT/BTCUSDT-trades-2026-02-12.zip.CHECKSUM" | head`
- Observed (excerpt):
  - `26e7c804...  BTCUSDT-trades-2026-02-12.zip`
- Command: `sha256sum services/ingestion/binance-vision-service/data_download/futures/um/daily/trades/BTCUSDT/BTCUSDT-trades-2026-02-12.zip`
- Observed (excerpt):
  - `26e7c804...  .../BTCUSDT-trades-2026-02-12.zip`

### Evidence 6: repair CLI 已加入入口

- Command: `cd services/ingestion/binance-vision-service && python3 -m src --help | head`
- Observed (excerpt):
  - `usage: binance-vision-service [-h] [--version] {collect,backfill,repair} ...`

### Evidence 7: 单测通过（含 checksum + repair）

- Command: `cd services/ingestion/binance-vision-service && pytest -q`
- Observed (excerpt):
  - `14 passed`
