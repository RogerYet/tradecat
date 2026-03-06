# PLAN：方案选择与落地路径

## 1) 目标（唯一语义）

把“币种查询子表”从“靠人工 bump + 靠运气不触发 400”收敛为：

1. **任何 layout 变更都会触发全量样式重刷**（不会残留旧格式）
2. **任何 compact grid 收缩都不会触发结构性 400**（不变量自动纠偏）
3. **冻结区观感一致**（banner/meta/header 行统一、目录单行溢出显示）

## 2) 技术选型对比

### 2.1 样式刷新触发（need_style）方案

| 方案 | 做法 | Pros | Cons |
| :-- | :-- | :-- | :-- |
| A. 手动 bump `style_version` | 每次 layout 改动都改常量（如 `symbol_table_v13→v14`） | 最小改动、最快止血 | 人工易漏；“多世界分裂”风险高（某个分支漏改就坏） |
| B. 自动 `style_signature`（推荐） | 用 banner/meta/header/frozen/placeholder 等关键参数生成签名；签名变化=必重刷 | 自动化、可扩展；减少人为失误 | 需要设计签名字段集合；实现略多 |
| C. 每轮强制全量重刷 | 每次导出都全量 repeatCell/updateDimension | 逻辑简单 | 配额与耗时不可控；弱网下失败概率更高 |

**选择**：B（自动 `style_signature`）  
**止血兜底**：保留 A 作为紧急手段（签名逻辑失效时可直接 bump）。

### 2.2 compact grid 不变量收敛点

| 方案 | 做法 | Pros | Cons |
| :-- | :-- | :-- | :-- |
| A. 在每个调用点 clamp | 所有调用 `_set_sheet_grid_properties` 的地方自己保证 row/col > frozen | 改动局部可见 | 易漏；调用点增多后不可控 |
| B. 在 `_set_sheet_grid_properties` 内统一 clamp（推荐） | 作为唯一 choke point：接收 row/col/frozen → 统一纠偏 | 一次改动全局收益；不会漏 | 需要明确不变量（并写测试/自检） |

**选择**：B。调用点可保留“意图清晰”的最小 clamp（但不是安全依赖）。

## 3) 关键数据流（ASCII）

```text
export_symbol_query_sheet()
  └─ values (2D) + merge_ranges + panel_blocks/header_row_0 + n_rows/n_cols
       └─ SaSheetsWriter.write_symbol_query_tab()
            ├─ ensure_grid_size(n_rows,n_cols)
            ├─ values.update(A1:...)
            ├─ (need_style) => repeatCell/columnWidth/frozen/... + meta(style_signature)
            ├─ compact grid => _set_sheet_grid_properties(rowCount/colCount/frozen)
            │                  └─ (choke point) enforce invariants (row>frozen, col>frozen)
            ├─ merges(mergeCells)
            └─ directory richtext (updateCells)
```

## 4) 原子变更清单（不写代码，只写落点）

1) `SaSheetsWriter.write_symbol_query_tab`  
   - 引入/更新 `style_signature`（或 bump style_version），确保 banner/meta/header/frozen/placeholder 变更必触发 need_style。
   - 当 `SHEETS_SYMBOL_QUERY_COMPACT_GRID=1` 时，`styled_rows/style_cols` 的元数据必须对齐实际 `n_rows/n_cols`，避免“历史 800 行锁死”。

2) `SaSheetsWriter._set_sheet_grid_properties`  
   - 统一 clamp：`rowCount >= frozenRowCount + 1`、`columnCount >= frozenColumnCount + 1`（以及 `>=1` 下限）。
   - 对“纠偏发生”输出单行 debug（可 grep），便于排障。

3) （可选）新增只读自检入口  
   - `python -m src --doctor`：打印每个 symbol tab 的 gridProperties/style_signature/last_error（不写入）。

4) 分支/部署对齐  
   - 若修复已在 `origin/dev`，将其 **cherry-pick/merge** 到长期维护分支（例如 `develop`）并更新文档，避免“修了又坏”。

## 5) 回滚协议（必须可自愈）

1) 紧急止血：禁用 compact grid（避免 400）
```bash
export SHEETS_SYMBOL_QUERY_COMPACT_GRID=0
```

2) 若样式签名逻辑误触发导致配额压力：
   - 临时回退为手动 bump + 控制只在 `--force` 时全量重刷

3) 完整回滚：
   - revert 本任务相关 commit（只涉及 sheets-service）
   - 重新运行一次 `python -m src --once --force --write-mode sa` 验证恢复

