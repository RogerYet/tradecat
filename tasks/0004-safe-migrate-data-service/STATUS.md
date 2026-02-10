# STATUS - 进度真相源（执行汇报写在这里）

状态: Done

## 证据存证模板

> 本文件已写入一次“真实执行汇报”（仅迁移目标新结构；源仓库未改动）。

### Step 1 - 冻结源仓库基线

- 命令: `stat /home/lenovo/.projects/tradecat/config/.env`
- 输出:
  - Modify: 2026-02-01 08:39:43.305830984 +0800
  - Size: 7964
  - Mode: 0600
- 命令: `sha256sum /home/lenovo/.projects/tradecat/config/.env`
- 输出:
  - `dd97d287ad8df00346915152bcfd85a6fa6b4a5be997d10f6b6b30293772b70e  /home/lenovo/.projects/tradecat/config/.env`

### Step 2 - rsync dry-run

- 命令: `rsync -an --delete --exclude '.venv/' --exclude '__pycache__/' --exclude 'logs/' --exclude 'pids/' --exclude '.pytest_cache/' ... | head -n 80`
- 输出:
  - （无输出，表示将要同步的差异为空或被 head 截断前为空；以实际 rsync 返回码为准）

### Step 3 - rsync 实际复制

- 命令: `rsync -a --delete --exclude '.venv/' --exclude '__pycache__/' --exclude 'logs/' --exclude 'pids/' --exclude '.pytest_cache/' /home/lenovo/.projects/tradecat/services/data-service/ /home/lenovo/tradecat/services/data-service/`
- 输出:
  - 返回码: 0
- 目标文件快照（部分）：
  - `src/__main__.py`
  - `src/config.py`
  - `scripts/start.sh`
  - `requirements.txt`

### Step 4 - 最小运行验证

- 命令: `cd /home/lenovo/tradecat/services/data-service && python3 src/__main__.py --help`
- 输出（节选）:
  - `usage: __main__.py [-h] [--ws] [--metrics] [--backfill] [--all]`
  - `--ws        WebSocket 采集`
  - `--all       全部启动`

### Step 5 - 复核源仓库未污染

- 命令: `cd /home/lenovo/.projects/tradecat && git diff --name-only -- services/data-service`
- 输出: （为空）
- 命令: `sha256sum /home/lenovo/.projects/tradecat/config/.env`
- 输出:
  - `dd97d287ad8df00346915152bcfd85a6fa6b4a5be997d10f6b6b30293772b70e  /home/lenovo/.projects/tradecat/config/.env`

### Step 6 - 迁移约束自检（目录与排除项）

- 命令: `test -f /home/lenovo/tradecat/services/data-service/src/config.py && echo OK`
- 输出: `OK`
- 命令: `test -d /home/lenovo/tradecat/libs/database/csv && echo OK`
- 输出: `OK`
- 命令: `test -d /home/lenovo/tradecat/services/data-service/.venv && echo HAS_VENV || echo NO_VENV`
- 输出: `NO_VENV`
