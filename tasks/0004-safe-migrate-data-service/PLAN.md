# PLAN - data-service 安全迁移路径

## 1) 方案对比

### 方案 A：直接抽到 `tradecat/ingestion/`（按新三层结构重写）

Pros:
- 结构最纯，立刻满足新宪法的单向依赖边界

Cons:
- 迁移成本与不确定性高（需要一次性理解 ws/backfill/metrics 三条链路）
- 初期缺少可运行验证点，风险大

### 方案 B：Lift-and-Shift（复制到新结构 services/ 下，保持根路径推导不变）

Pros:
- 风险最低：保持 `PROJECT_ROOT` 推导方式不变
- 最快得到“可运行的最小证据”（--help / dry-run）

Cons:
- 目标结构中会存在 legacy 目录（`services/`），需要后续再收敛

**选择**：方案 B（先迁移可运行，再逐步收敛）。

---

## 2) 原子变更清单（执行 Agent 按顺序执行）

1) 冻结源仓库基线（只读证据）：
   - `config/.env` 的 mtime/size/hash
   - （可选）`services/data-service/src/config.py` 的 hash（证明未改）
2) 在新结构创建目录：
   - `/home/lenovo/tradecat/services/`
   - `/home/lenovo/tradecat/libs/database/csv`
3) rsync 复制（强制排除）：
   - 排除：`.venv/`, `__pycache__/`, `logs/`, `pids/`, `.pytest_cache/`
4) 最小运行验证：
   - `python3 src/__main__.py --help`
5) 再次核对源仓库基线不变（防误写）。

---

## 3) 回滚协议

- 若任何 Gate 失败：
  1) 停止执行
  2) 删除目标目录 `/home/lenovo/tradecat/services/data-service`
  3) 重新从 rsync dry-run 开始
- 若发现源仓库文件 mtime/hash 变化：
  1) 立即停止
  2) 在 `STATUS.md` 记录差异证据
  3) 定位“写入路径来自哪里”（通常是 `PROJECT_ROOT` 推导错误）

