# CONTEXT：现状、根因与风险图谱

## 1) 现状（用户可见症状）

- 服务器端 sheets-service “看起来挂了”：币种查询子表不更新/导出失败。
- 币种查询表顶部冻结区样式错位：表头背景色不一致、冻结条消失或冻结行列不符合预期。
- 版式变更后（例如新增 banner 首行广告位、目录合并为单行）只有部分 tab 生效，其他 tab 残留旧样式。

## 2) 关键根因（证据驱动）

### 2.1 样式刷新触发条件（need_style）存在“历史 styled_rows/cols 锁死”问题

位置：`services/consumption/sheets-service/src/sa_sheets_writer.py:1850-1881`

- `style_version` 固定为 `symbol_table_v13`，只要未 bump 就无法强制全量重刷。  
- `target_rows/cols` 的计算会把历史 `styled_rows/cols` 带进来：
  - `target_rows = max(n_rows, styled_rows, 1)`（`sa_sheets_writer.py:1874`）
  - `need_style` 依赖 `target_rows > styled_rows` 与 `target_cols != styled_cols`（`sa_sheets_writer.py:1876-1881`）

当历史 `styled_rows` 很大（典型：旧版本写死过 800），且本次导出的 `n_rows` 更小，则：
- `target_rows == styled_rows`，导致 `need_style` 不触发；
- layout/冻结行数/表头行背景色等变更无法“全量刷新”，只会写 values，不会覆盖格式 → 出现“部分 tab 还是旧的”。

### 2.2 compact grid 收缩缺少结构性不变量 → 触发 Sheets API 400（导出中断）

位置：
- `services/consumption/sheets-service/src/sa_sheets_writer.py:2794-2815`（币种查询 tab 的 compact grid）
- `services/consumption/sheets-service/src/sa_sheets_writer.py:9530-9594`（`_set_sheet_grid_properties`）

当前实现会把 `rowCount/columnCount` 直接收缩到 `n_rows/n_cols`：
- `want_rows = n_rows`，`want_cols = n_cols`（`sa_sheets_writer.py:2806-2807`）
- 然后调用 `_set_sheet_grid_properties(row_count=want_rows, col_count=want_cols, frozen_*=...)`（`sa_sheets_writer.py:2809-2815`）

但 `_set_sheet_grid_properties` 仅做 `>=1` 的下限（`sa_sheets_writer.py:9565-9576`），缺少硬约束：
- `rowCount >= frozenRowCount + 1`
- `columnCount >= frozenColumnCount + 1`

当 `n_rows/n_cols` 在空表/极端数据/临时结构下接近冻结行列数时，会触发结构性 400（典型报错语义：不能删光非冻结行/列），导致整轮导出中断 → 用户看到“服务死了”。

### 2.3 分支漂移：修复可能只在 `origin/dev` 存在，`develop` 未对齐

证据命令（本地执行）：

```bash
git branch -avv
```

当前 repo 状态（示例输出）显示：
- `develop` 与 `origin/dev` 不同 commit；`origin/dev` 已包含修复提交（示例：`fix(sheets): align symbol tabs frozen header styles`）。

## 3) 风险量化表

| 风险点 | 严重程度 | 触发信号 (Signal) | 缓解方案 (Mitigation) |
| :--- | :--- | :--- | :--- |
| 样式不刷新导致冻结区错位 | High | 币种查询 tab 表头背景不一致/冻结条缺失 | 引入 `style_signature`（或 bump 机制）确保 layout 变更必触发全量重刷 |
| compact grid 触发 400 导出中断 | High | 日志出现 `HttpError 400` / 导出进程退出码非 0 | 在 `_set_sheet_grid_properties` 内统一收敛不变量，所有调用点自动纠偏 |
| 分支漂移导致“修了又坏” | Medium | 服务器端与本地分支不同步 | 明确部署分支；用 cherry-pick/merge 把修复落到长期维护分支 |
| 弱网/代理抖动导致间歇失败 | Medium | `SSLError/ConnectionResetError/Timeout` | 保持幂等写入；对读写请求做限次退避重试；减少每轮写入请求数 |

## 4) 假设与证伪（Safe-Inference）

1) 假设：币种查询子表默认启用 compact grid（`SHEETS_SYMBOL_QUERY_COMPACT_GRID=1`）。  
Verify：
```bash
rg -n \"SHEETS_SYMBOL_QUERY_COMPACT_GRID\" -S services/consumption/sheets-service/src/sa_sheets_writer.py
```

2) 假设：币种查询冻结行列依赖 `header_row_0` 与 `_symbol_query_frozen_cols()`。  
Verify：
```bash
rg -n \"_symbol_query_frozen_cols\\(|header_row_0\" services/consumption/sheets-service/src/sa_sheets_writer.py
```

3) 假设：服务部署使用 `origin/dev` 分支（而非 `develop`）。  
Verify（服务器上）：
```bash
git -C /home/nvidia/.projects/tradecat rev-parse --abbrev-ref HEAD
git -C /home/nvidia/.projects/tradecat log -1 --oneline
```

## 5) 影响面（需要一起改的地方）

- `SaSheetsWriter.write_symbol_query_tab()`：样式刷新、冻结行列、compact grid、目录 RichText。
- `SaSheetsWriter._set_sheet_grid_properties()`：统一不变量（关键收敛点，必须保证所有调用点安全）。
- 可能的其他托管 tab（看板/Polymarket）若复用 `_set_sheet_grid_properties`，也会受益于不变量收敛。

