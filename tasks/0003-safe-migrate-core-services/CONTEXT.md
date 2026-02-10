# CONTEXT - 安全迁移（只读源仓库）

## 1) 现状追溯（基于证据，不做臆测）

### 1.1 源仓库与目标路径

- 源仓库：`/home/lenovo/.projects/tradecat`
- 核心服务目录：`/home/lenovo/.projects/tradecat/services/`
  - 证据：`ls -la services` 显示 `ai-service,data-service,signal-service,telegram-service,trading-service,aws-service`
- API 服务：`/home/lenovo/.projects/tradecat/services-preview/api-service/`
  - 证据：`ls -la services-preview/api-service`
- 新结构目标：`/home/lenovo/tradecat/`，代码包目录：`/home/lenovo/tradecat/tradecat/`
  - 证据：`ls -la /home/lenovo/tradecat/tradecat | head`

### 1.2 各服务入口与关键耦合点（用于迁移风险评估）

> 下面引用的路径/行号均来自 `nl -ba ...` 输出，可由执行 Agent 复核。

- `data-service`
  - 入口调度器：`services/data-service/src/__main__.py:23`（Scheduler）到 `:86`（run loop）
  - .env 加载：`services/data-service/src/config.py:14`（读取 `PROJECT_ROOT/config/.env`）
- `trading-service`
  - 入口与 CLI：`services/trading-service/src/__main__.py:28`~`:109`
  - **潜在路径错误风险**：`services/trading-service/src/__main__.py:19` 使用 `Path(__file__).parents[1] / "config" / ".env"`，但源仓库中不存在 `services/trading-service/config/.env`（证据：`ls -la services/trading-service/config` → No such file）
- `signal-service`
  - 支持 SQLite/PG 引擎：`services/signal-service/src/__main__.py:5`~`:137`
  - 数据路径/覆盖能力：`services/signal-service/src/config.py:28`（`INDICATOR_SQLITE_PATH` 可覆盖）与 `:39`（`SIGNAL_HISTORY_DB_PATH` 可覆盖）
- `telegram-service`
  - 入口：`services/telegram-service/src/__main__.py:16` 调用 `bot.app:main`
  - **强耦合 REPO_ROOT + .env**：`services/telegram-service/src/bot/app.py:26`~`:43`（推导 `REPO_ROOT` 并加载 `config/.env`）
  - **高风险写入行为**：`services/telegram-service/src/bot/env_manager.py:22`~`:24` 定义 `ENV_PATH = .../config/.env`，且模块描述为“通过 Bot 管理 .env 配置”
- `ai-service`
  - 入口会注入 `REPO_ROOT` 到 `sys.path`：`services/ai-service/src/__main__.py:21`~`:26`
  - 依赖共享库：`services/ai-service/src/llm/client.py:56`（引用 `libs.common`）
  - SQLite 读指标库：`services/ai-service/src/config.py:25`
- `api-service`
  - 入口：`services-preview/api-service/src/__main__.py:13`~`:19`（uvicorn 启动）
  - 默认读取 `PROJECT_ROOT/config/.env`：`services-preview/api-service/src/config.py:11`~`:15`

### 1.3 依赖与路径耦合的“迁移现实”

在源仓库中，多个服务通过以下方式共享代码/数据：

- `sys.path` 注入（跨服务/跨仓库根目录）：
  - `services/telegram-service/src/bot/app.py:33`~`:38`
  - `services/ai-service/src/__main__.py:23`~`:26`
- 共享库 `libs/common`（被 telegram/ai 引用）：
  - `services/telegram-service/src/bot/app.py:53`（`libs.common.i18n`）
  - `services/ai-service/src/llm/client.py:56`
- 共享 SQLite 数据文件（必须避免污染源仓库数据文件）：
  - `services/signal-service/src/config.py:36` 默认指向 `libs/database/services/telegram-service/market_data.db`
  - `services/trading-service/src/core/storage.py:15`（写 `market_data.db`，高风险）

结论：迁移不能只“复制 services 目录”，必须同时处理：

- 配置根目录（新结构必须有自己的 `config/.env`，且禁止回写源仓库）
- SQLite 输出路径（必须改为新结构下独立路径或使用环境变量覆盖）
- `libs/common` 的依赖供给（复制或以 `PYTHONPATH` 明确注入）

## 2) 约束矩阵（强制）

| 约束 | 来源 | 迁移影响 |
| :-- | :-- | :-- |
| **不修改源仓库业务代码** | 用户指令 | 只能通过“拷贝到新目录后再改”实现迁移与重构 |
| `config/.env` 视为生产配置（只读） | `AGENTS.md`（仓库规则） | 源仓库 `config/.env` 必须保持不变；新结构需自建自己的 `.env` |
| 禁止修改敏感 SQLite DB（源仓库） | `AGENTS.md` + 用户安全迁移要求 | trading/signal 写入路径必须指向新结构，不得写入源仓库 `libs/database/...` |

## 3) 风险量化表（只列“会炸”的）

| 风险点 | 严重程度 | 触发信号 (Signal) | 缓解方案 (Mitigation) |
| :--- | :---: | :--- | :--- |
| 迁移后仍指向源仓库 `.env` | High | 新服务运行时读取/写入 `/home/lenovo/.projects/tradecat/config/.env` | 新结构自建 `config/.env`，并通过目录推导/环境变量确保 REPO_ROOT 指向新结构 |
| 迁移后写入源仓库 SQLite | High | `market_data.db` 文件 mtime 变化或 WAL 出现 | 强制设置 `INDICATOR_SQLITE_PATH` 指向新结构；源仓库 DB 文件权限只读（执行时） |
| sys.path 注入导致“跑到了旧代码” | High | 运行时打印路径指向 `.projects/tradecat` | 迁移后禁止把旧仓库根加入 `PYTHONPATH`；新结构目录必须在 sys.path 最前 |
| api-service 连接池/依赖缺失 | Medium | uvicorn 启动报 `ImportError` | 在新结构中按 service 维持依赖隔离（优先保持原 requirements） |

## 4) 假设与证伪（最小假设推进）

| 假设 | 默认假设 | 证伪命令 |
| :-- | :-- | :-- |
| 新结构根目录可写 | 是 | `test -w /home/lenovo/tradecat && echo OK` |
| 源仓库 services 目录只读即可完成迁移 | 是 | `find services -maxdepth 2 -type f | head` |
| 可以通过环境变量覆盖 SQLite 写入路径 | 是 | `rg -n \"INDICATOR_SQLITE_PATH\" -S services/trading-service/src services/signal-service/src | head` |

