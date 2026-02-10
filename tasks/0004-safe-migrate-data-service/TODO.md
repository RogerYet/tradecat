# TODO - data-service 迁移执行清单

[ ] P0: 冻结源仓库基线（config/.env） | Verify: `stat /home/lenovo/.projects/tradecat/config/.env` | Gate: `STATUS.md` 记录 mtime/size/hash
[ ] P0: 证明未改源业务代码 | Verify: `cd /home/lenovo/.projects/tradecat && git diff --name-only -- services/data-service` | Gate: 输出为空

[ ] P0: 创建目标目录（固定到 services/ 下） | Verify: `mkdir -p /home/lenovo/tradecat/services /home/lenovo/tradecat/libs/database/csv && echo OK` | Gate: OK
[ ] P0: rsync dry-run（排除项必须生效） | Verify: `rsync -an --delete --exclude '.venv/' --exclude '__pycache__/' --exclude 'logs/' --exclude 'pids/' --exclude '.pytest_cache/' /home/lenovo/.projects/tradecat/services/data-service/ /home/lenovo/tradecat/services/data-service/ | head -n 50` | Gate: 输出不包含 `.venv/` 等排除目录
[ ] P0: rsync 实际复制 | Verify: `rsync -a --delete --exclude '.venv/' --exclude '__pycache__/' --exclude 'logs/' --exclude 'pids/' --exclude '.pytest_cache/' /home/lenovo/.projects/tradecat/services/data-service/ /home/lenovo/tradecat/services/data-service/` | Gate: 退出码 0

[ ] P1: 最小运行验证（help） | Verify: `cd /home/lenovo/tradecat/services/data-service && python3 src/__main__.py --help` | Gate: 输出包含 `--ws` 或 `--all`
[ ] P1: 复核源仓库基线不变 | Verify: `stat /home/lenovo/.projects/tradecat/config/.env` | Gate: 与迁移前记录一致

Parallelizable:
- rsync 复制与最小运行验证可串行完成；本任务不建议并行（优先可证伪）。

