# ACCEPTANCE - 安全迁移验收标准

## A. 原子断言（Atomic Assertions）

### A1. 源仓库保持“只读不污染”

- [ ] 迁移全过程中，源仓库以下文件/目录不发生变更：
  - `/home/lenovo/.projects/tradecat/config/.env`
  - `/home/lenovo/.projects/tradecat/libs/database/services/**`（尤其是 `market_data.db`、`cooldown.db`、`signal_history.db`）
  - `/home/lenovo/.projects/tradecat/services/**`（业务代码保持不变）
  - `/home/lenovo/.projects/tradecat/services-preview/api-service/**`（业务代码保持不变）
- Verify（执行 Agent）：`cd /home/lenovo/.projects/tradecat && git status --porcelain`
- Gate：
  - `git diff --name-only -- services services-preview/api-service` 输出为空（证明未改业务代码）
  - 关键文件 mtime/hash 不变（在 `STATUS.md` 记录迁移前后对比口径）：`config/.env` + 关键 SQLite DB

### A2. 新结构具备“可跑的最小闭环”

对每个迁移服务满足至少一条“最小可运行”条件（不要求完整业务功能，但要求能启动/自检）：

- `signal-service`：`python -m src --test` 能输出“配置测试通过”（源仓库已有逻辑）
- `ai-service`：`python -m src --test` 能完成提示词注册自检（不要求 LLM 可用）
- `api-service`：`python -m src --help` 或 `python -m src` 能启动到端口（DEBUG 可关闭 reload）
- `data-service`：`python src/__main__.py --help` 可输出用法；或启动 `--ws` 不崩溃
- `trading-service`：`python -m indicator_service --once --symbols BTCUSDT --intervals 1m` 可进入主流程（允许因外部依赖缺失而提前失败，但必须可定位）
- `telegram-service`：允许不连 Telegram（无 token）时能加载配置并在缺少 token 时给出清晰错误（需要在迁移后的新结构中实现“最小运行模式”或跳过启动）

### A3. 配置与写入路径隔离

- [ ] 新结构存在独立的 `config/.env`（不复制源仓库密钥），并且迁移服务默认只读取新结构的 `.env`
- [ ] 所有会写 SQLite 的服务必须写入新结构内路径（例如 `/home/lenovo/tradecat/libs/database/...`），不得写入源仓库

## B. 边缘路径（至少 3 个）

1) **新结构中缺少 psycopg/psycopg_pool**：服务应给出可读错误，不得误写源仓库。  
2) **旧代码 sys.path 注入**：必须能在 STATUS 中定位到“路径来自何处”，并给出修复步骤。  
3) **Telegram 服务潜在写 `.env`**：必须通过文件权限/路径隔离避免写入源仓库 `.env`。  

## C. 禁止性准则（Anti-Goals）

- 不允许为了迁移通过而修改源仓库服务代码。
- 不允许在源仓库路径下新建/覆盖任何生产配置或数据库文件。
- 不允许把“新结构迁移成功”建立在“仍引用旧仓库根目录作为运行时依赖”的基础上（除非显式记录为临时豁免）。
