# TODO - 迁移执行清单（只读源仓库）

[ ] P0: 创建新结构迁移工作区 | Verify: `ls -la /home/lenovo/tradecat` | Gate: 存在 `migrated/` 目录（空也可）
[ ] P0: 冻结源仓库基线（hash/mtime） | Verify: `stat /home/lenovo/.projects/tradecat/config/.env` | Gate: `STATUS.md` 记录 `config/.env` 与关键 SQLite 的迁移前后对比口径
[ ] P0: 证明“未改业务代码”（只读约束） | Verify: `cd /home/lenovo/.projects/tradecat && git diff --name-only -- services services-preview/api-service` | Gate: 输出为空
[ ] P0: dry-run 复制清单（排除项生效） | Verify: `rsync -an ...` | Gate: 输出中不包含 `.venv/`、`libs/database/services/*.db`、`config/.env`

[ ] P0: 复制 5 个核心服务（排除 aws-service） | Verify: `find /home/lenovo/tradecat/migrated -maxdepth 2 -type d -name src | wc -l` | Gate: 数量=5（data/trading/signal/telegram/ai）
[ ] P0: 复制 api-service | Verify: `test -f /home/lenovo/tradecat/migrated/api-service/src/app.py && echo OK` | Gate: OK

[ ] P1: 新结构创建独立 `config/.env`（不含密钥） | Verify: `ls -la /home/lenovo/tradecat/config/.env` | Gate: 权限 600，且不等于源仓库内容（hash 不同）
[ ] P1: 新结构创建独立 SQLite 输出目录 | Verify: `find /home/lenovo/tradecat/libs/database/services -maxdepth 3 -type d | head` | Gate: 目录存在且无源仓库 DB 文件
[ ] P1: 强制覆盖写入路径（INDICATOR_SQLITE_PATH 等） | Verify: `env | rg 'INDICATOR_SQLITE_PATH|SIGNAL_HISTORY_DB_PATH'` | Gate: 都指向 `/home/lenovo/tradecat/...`

[ ] P1: 逐服务最小启动验证（按 PLAN Phase 3 顺序） | Verify: `python -m ... --test` | Gate: 失败必须可定位且不写入源仓库

[ ] P2: 建立“防误写”门禁（可选） | Verify: `md5sum`/`stat` 对比 | Gate: 源仓库关键文件 hash/mtime 不变

Parallelizable:
- P0 复制可以并行（每个服务独立 rsync），但必须先完成源仓库基线冻结。
