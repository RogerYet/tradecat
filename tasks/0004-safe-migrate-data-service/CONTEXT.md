# CONTEXT - data-service 迁移约束与风险图谱

## 1) 源与目标（证据）

- 源服务：`/home/lenovo/.projects/tradecat/services/data-service/`
- 目标服务：`/home/lenovo/tradecat/services/data-service/`

## 2) data-service 的“根路径推导”机制（决定迁移目录形态）

`services/data-service/src/config.py` 使用以下逻辑推导项目根目录（摘录以证据为准）：

- `SERVICE_ROOT = Path(__file__).parent.parent`（`src/config.py` → `data-service/`）
- `PROJECT_ROOT = SERVICE_ROOT.parent.parent`（期望指向仓库根）
- .env 加载：`PROJECT_ROOT / "config" / ".env"`
- 默认输出目录：
  - 日志：`PROJECT_ROOT/services/data-service/logs`
  - 数据：`PROJECT_ROOT/libs/database/csv`

因此，**目标路径必须保证**：

- `.../services/data-service` 的上两级目录是新结构根 `/home/lenovo/tradecat`
- 否则 `PROJECT_ROOT` 会被推导成错误目录，产生“读旧 .env / 写旧目录”的高风险

结论：本任务目标必须是：

- `/home/lenovo/tradecat/services/data-service`（而不是 `/home/lenovo/tradecat/migrated/data-service`）

## 3) 风险量化表

| 风险点 | 严重程度 | 触发信号 (Signal) | 缓解方案 (Mitigation) |
| :--- | :---: | :--- | :--- |
| `PROJECT_ROOT` 推导错误，导致访问源仓库 | High | 运行时创建/写入 `.projects/tradecat/services/data-service/logs` 或读取 `.projects/tradecat/config/.env` | 目标路径固定为 `/home/lenovo/tradecat/services/data-service`；迁移前后记录 mtime/hash |
| 复制时带入 `.venv/` 导致环境污染/体积暴涨 | Medium | 目标目录出现 `.venv/` | rsync 排除 `.venv/`、`__pycache__/`、`logs/`、`pids/` |
| 目标结构缺少 `libs/database/csv` 导致运行时自动建到异常位置 | Low | 创建目录失败或落在非预期根目录 | 在新结构预先创建 `libs/database/csv`（空目录即可） |

## 4) 假设与证伪

| 假设 | 默认假设 | 证伪命令 |
| :-- | :-- | :-- |
| 目标新结构可写 | 是 | `test -w /home/lenovo/tradecat && echo OK` |
| data-service 不会写入 `.env` | 是 | `rg -n \"write.*\\.env|ENV_PATH\" services/data-service/src | head`（仅证伪写入行为是否存在） |
| `python3` 可用 | 是 | `python3 --version` |

