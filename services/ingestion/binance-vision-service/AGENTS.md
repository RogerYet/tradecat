# binance-vision-service 开发约束（强制）

本文件的作用域：`services/ingestion/binance-vision-service/**`。

> 结论先行：这里的目标不是“尽快采到一些数据”，而是**严格对齐 Binance Vision 的数据产品**，把它变成一套可读、可追溯、可增量、可复现实验的 Raw 事实层。

## 0. 目标（必须同时满足）

- **实时采集实现**：只允许使用 `ccxt` / `ccxtpro`。
- **实时优先**：实时采集必须优先走 `ccxtpro` WebSocket；只有在“该数据集没有可用 WS 能力”时才允许 REST。
- **结构对齐**：目录层级、文件命名、CSV 字段必须与 `data.binance.vision` **严格一致**（学习向：人类一眼能对照官方）。
- **字段完备**：采集入库的数据必须包含该数据集官方 CSV 的全部字段（字段名或语义映射一致）；缺字段必须补齐（可计算则计算），否则禁止“半字段入库”。
- **物理层只收基元（Raw/Atomic）**：只写入 `crypto.raw_*` 表；`crypto.agg_*`（可派生/汇总）一律延后或由独立流程生成。
- **历史回填**：允许直接下载 Binance Vision 的 `daily/monthly` ZIP 作为权威来源（用于“从 2019 到现在”的全量补齐与最终对账）。

## 1. 禁止事项（Hard No）

- 禁止引入除 `ccxt/ccxtpro` 以外的交易所 SDK/HTTP 客户端去“绕过”字段缺失。
- 禁止在实时链路中用 REST 替代 WS（除非明确证明该数据集无 WS）。
- 禁止在本服务里创建/维护派生层（`aggTrades/klines/*Klines` 等）物理表或写入逻辑。
- 禁止修改 `config/.env`（只读）；只允许读取环境变量（由顶层脚本安全加载）。
- 禁止把运行时数据目录（`data/`、`data_download/`）加入 Git。
- 禁止添加未经验证的第三方依赖（新增依赖必须先证明 repo 内无同类能力且有明确收益）。

## 2. “官方目录 = 代码目录”的镜像规则（核心约束）

你必须把 `data.binance.vision` 的目录结构当成**数据契约**，并在代码里做 1:1 镜像：

- 实时采集卡片（realtime）：`src/collectors/crypto/data/**`
- 历史下载/补齐卡片（download/backfill）：`src/collectors/crypto/data_download/**`

规则：**一个 CSV 数据集 = 一个采集器卡片 = 一个 Python 文件**。

示例（官方 → 代码）：

- `data/futures/um/daily/trades/...` → `src/collectors/crypto/data/futures/um/trades.py`
- `data/futures/um/daily/bookTicker/...` → `src/collectors/crypto/data/futures/um/bookTicker.py`
- `data/option/daily/EOHSummary/...` → `src/collectors/crypto/data/option/EOHSummary.py`

## 3. 运行时落盘目录（与“代码目录”严格区分）

本 repo 中的 `src/collectors/**` 是**代码**；运行时输出的 CSV 文件必须落在服务根目录下的：

- `services/ingestion/binance-vision-service/data/**`（实时落盘）
- `services/ingestion/binance-vision-service/data_download/**`（历史下载落盘）

注意：这两个目录允许在运行时自动创建，但**不得提交**（应保持被忽略）。

## 4. 数据库契约（DDL 是唯一真相源）

- 原子/物理层（Raw/Atomic）DDL：`libs/database/db/schema/009_crypto_binance_vision_landing.sql`
- 派生/汇总层（Derived，可选）DDL：`libs/database/db/schema/011_crypto_binance_vision_derived.sql`
- 文件追溯表（必须用）：`libs/database/db/schema/008_multi_market_core_and_storage.sql`（`storage.files`）
- 采集治理旁路表（run/watermark/gap）：`libs/database/db/schema/012_crypto_ingest_governance.sql`

关键规则：

- **只写 `crypto.raw_*`**（当前阶段）。
- 表名不写 `daily/monthly`；频率由 `storage.files.frequency` 表达。
- 落库幂等：推荐 `ON CONFLICT ...` + 正确主键/唯一键。
- 允许旁路治理写入 `crypto.ingest_runs` / `crypto.ingest_watermark` / `crypto.ingest_gaps`（这些不是行情事实表）。

### 4.1 特例：`crypto.raw_futures_um_trades`（实时+回填统一事实表）

你已明确该表字段极简（不放 `file_id/ingested_at/time_ts`），并要求：

- 实时（WS）与历史回填（Vision ZIP）都写入同一张表；
- 回填（官方）允许受控 UPDATE 修正差异列；
- 表内 `symbol` 统一为 Binance 原生 `BTCUSDT` 形式。

因此：该表不强制逐行 `file_id` 追溯；文件追溯只保留在“下载落盘路径/导入任务日志”层面。

## 5. 编码规范（面向可维护）

- 对人可见文本（日志/文档/注释）用中文；代码结构/标识符用简洁英文。
- 任何采集器必须显式处理：
  - 断线重连（指数退避上限）
  - 限速/节流（必要时）
  - 资源释放（`await exchange.close()`）
  - 幂等写入（文件与数据库）
- 控制复杂度：尽量消除“特殊情况分支”；出现 3 个以上分支判断，优先重构数据结构/流程。

## 6. 你新增一个数据集时的最小流程（MVP）

1) 在镜像目录下新增卡片文件（realtime 或 download）。
2) 明确该数据集的“官方相对路径模板”（用于 `storage.files.rel_path`）。
3) 明确 CSV 字段（顺序/类型/时间单位），并在卡片 docstring 写清楚“样本事实”。
4) 只做字段对齐与事件流产出；落盘/落库走 writer（保证幂等与可追溯）。
5) 最少写 1 个冒烟测试（不需要接真实交易所，测试路径拼接/字段转换/幂等键）。
