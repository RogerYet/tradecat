# PLAN - 迁移架构决策与路径（只读源仓库）

## 1) 技术路线对比（至少两个方案）

### 方案 A：立即按三层结构“重写/抽取”

Pros:
- 结构最干净，短期内就满足宪法与分层契约

Cons:
- 风险极高：需要同时理解 6 个服务 + 共享库 + 数据路径语义
- 很难保证“不污染源仓库数据”
- 容易在迁移初期失去可运行性（无法验证）

### 方案 B：Lift-and-Shift（先复制再收敛）

Pros:
- 风险最低：先把“运行闭环”迁到新结构，再逐步重构
- 更适配 Agent-Coding：每次改动局部化、可验证、可回滚

Cons:
- 新结构初期会存在 `sys.path` hack 与 legacy 目录
- 需要额外的门禁避免“legacy 蔓延”

**选择**：方案 B（先迁移可运行，再逐步收敛到三层契约）。

---

## 2) 迁移分阶段（每阶段都可停、可回滚）

### Phase 0：冻结源仓库基线（只读证据）

- 记录源仓库版本与关键文件 hash/mtime（`.env`、关键 SQLite DB）
- 目的：后续可证明“未污染源仓库”

### Phase 1：复制服务到新结构（不改源仓库）

目标目录建议（保持服务自包含，避免 import 走旧仓库）：

- 新结构根：`/home/lenovo/tradecat/`
- 将每个服务复制到：`/home/lenovo/tradecat/migrated/<service-name>/`
  - 例如：`migrated/data-service/`, `migrated/trading-service/`...
  - 同时复制 `services-preview/api-service` → `migrated/api-service/`

复制策略（执行 Agent 需要先 `--dry-run`）：

- 必须排除：`.venv/`, `__pycache__/`, `logs/`, `pids/`, `run/`, `cache/`
- 必须禁止复制：源仓库 `config/.env`、源仓库 `libs/database/services/**.db`

### Phase 2：新结构独立配置与数据路径隔离

1) 新结构自建 `config/.env`（从 `.env.example` 派生，不含密钥，权限 600）  
2) 新结构自建 `libs/database/services/...`（只创建目录与新 DB 文件，不使用源仓库 DB）  
3) 对“读源仓库 SQLite”的服务改为只读挂载或显式复制到新结构（按服务不同策略）：
   - `trading-service`/`signal-service` 会写：必须写入新结构 DB（强制 `INDICATOR_SQLITE_PATH`）
   - `ai-service` 多为读：可以指向新结构 DB（与 trading 同源）或只读复制

### Phase 3：最小运行验证（逐服务）

按风险从低到高验证：

1) `signal-service --test`  
2) `ai-service --test`  
3) `api-service` 启动（不要求完整数据）  
4) `data-service` help/启动  
5) `trading-service` once  
6) `telegram-service`（要求“缺 token 时可读失败”，并确保不会写源仓库 `.env`）

### Phase 4：收敛到新结构三层（可选，另立子任务）

当 Phase 1-3 稳定后，再将 legacy 代码逐步拆入 `/home/lenovo/tradecat/tradecat/ingestion|compute|consumption`，以契约驱动替换 `sys.path` hack。

---

## 3) 回滚协议（100% 还原）

- 新结构目录可整体删除重来（因为不应写入源仓库）。
- 若发现源仓库文件被写入（mtime/hash 变化），必须立即停止并：
  1) 记录差异证据到 `STATUS.md`
  2) 将新结构中所有写入路径切断（权限只读/环境变量覆盖）
  3) 重新从 Phase 0 复制，直到验收通过

