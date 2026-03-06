# STATUS：进度真相源

状态机：Not Started / In Progress / Blocked / Done

## 当前状态：Done

## 已收集证据（Live Evidence）

### 仓库分支漂移

执行命令：

```bash
git branch -avv
```

关键观察（2026-03-06）：

- 本地：`develop` 指向 `df18ec2c docs: format public service links`
- 远端：`origin/dev` 指向 `4d9bfed0 fix(sheets): align symbol tabs frozen header styles`

### 关键代码位置（用于审计/落点）

- 样式触发条件（need_style）：`services/consumption/sheets-service/src/sa_sheets_writer.py:1850-1881`
  - `style_version = "symbol_table_v13"`（1852）
  - `target_rows = max(n_rows, styled_rows, 1)`（1874）
- compact grid 收缩：`services/consumption/sheets-service/src/sa_sheets_writer.py:2794-2815`
  - `want_rows = n_rows`，`want_cols = n_cols`（2806-2807）
  - `_set_sheet_grid_properties(row_count=want_rows, col_count=want_cols, frozen_*=...)`（2809-2815）
- 网格属性设置（缺不变量）：`services/consumption/sheets-service/src/sa_sheets_writer.py:9530-9594`
  - 仅 clamp `>=1`，未保证 `rowCount > frozenRowCount` / `colCount > frozenColumnCount`

### `_set_sheet_grid_properties()` 调用点清单（P0 审计）

执行命令：

```bash
rg -n "_set_sheet_grid_properties\\(" services/consumption/sheets-service/src/sa_sheets_writer.py
```

命中位置（2026-03-06，本地 `develop`）：

- `services/consumption/sheets-service/src/sa_sheets_writer.py:2375`（币种查询：每次对齐冻结行列）
- `services/consumption/sheets-service/src/sa_sheets_writer.py:2809`（币种查询：compact grid 裁剪 rowCount/colCount）
- `services/consumption/sheets-service/src/sa_sheets_writer.py:3515`（Polymarket：compact grid）
- `services/consumption/sheets-service/src/sa_sheets_writer.py:4923`（Polymarket：compact grid）
- `services/consumption/sheets-service/src/sa_sheets_writer.py:6184`（Polymarket：compact grid）
- `services/consumption/sheets-service/src/sa_sheets_writer.py:7257`（主看板 v5：compact grid）
- `services/consumption/sheets-service/src/sa_sheets_writer.py:7354`（dashboard_meta：收缩 grid）
- `services/consumption/sheets-service/src/sa_sheets_writer.py:7577`（cards_index：收缩 grid）
- `services/consumption/sheets-service/src/sa_sheets_writer.py:7783`（append-only：收缩 grid）
- `services/consumption/sheets-service/src/sa_sheets_writer.py:8220`（看板样式：对齐冻结行列）
- `services/consumption/sheets-service/src/sa_sheets_writer.py:8772`（看板/变体：compact grid）

结论：必须在 `_set_sheet_grid_properties()` 内做统一纠偏，否则任何一个调用点漏传 frozen/row/col 都可能触发结构性 400。

## 执行记录（2026-03-06）

### 1) 收敛 `_set_sheet_grid_properties` 的结构性不变量（避免 400）

变更点：

- `services/consumption/sheets-service/src/sa_sheets_writer.py:_set_sheet_grid_properties()`
  - 统一 clamp：`rowCount > frozenRowCount`、`columnCount > frozenColumnCount`（至少保留 1 行/列非冻结）
  - 同时支持“只更新 frozen，不更新 row/col”的场景：用当前 grid size 对冻结数做上限 clamp
  - debug 时输出单行：`sheets.grid_clamp ...`
- 补齐 3 个 shrink 调用点：显式传 `frozen_column_count=0`
  - `sa_sheets_writer.py:7354`、`:7577`、`:7783`

验证（只读/本地）：

```bash
cd services/consumption/sheets-service
make syntax
make lint
make test
```

结果：`8 passed`，ruff 检查通过。

### 2) 修复币种查询样式刷新锁死（历史 styled_rows=800）

变更点：

- `services/consumption/sheets-service/src/sa_sheets_writer.py:write_symbol_query_tab()`
  - 引入 `symtab.<tab>.style_signature`：缺失或变化即触发全量样式重刷
  - compact grid 开启时：样式覆盖范围按 `n_rows/n_cols` 收敛，避免历史 `styled_rows` 锁死

验证：同上（syntax/lint/tests）。

## 下一步（执行入口）

按 `TODO.md` 的 P0 顺序推进，并把每一步的命令输出（或关键片段）追加到本文件。
