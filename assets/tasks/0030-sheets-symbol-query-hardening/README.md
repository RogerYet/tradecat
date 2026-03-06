# 任务门户：sheets-symbol-query-hardening

## Why（价值，100字内）

修复 sheets-service 在“币种查询”子表上的结构性脆弱点：layout 变更（广告 banner/目录/冻结行列）后样式无法全量刷新、compact grid 裁剪触发 Sheets API 400 导致导出中断、冻结条/表头背景错位。把问题收敛为可复用的不变量与自检流程，避免未来再次“看起来服务挂了”。

## In Scope（范围）

- **样式刷新收敛**：避免“历史 styled_rows/cols 很大”导致 `need_style` 不触发；为 layout 变更提供可靠的全量刷新触发（`style_signature` 或等价机制）。
- **compact grid 不变量**：任何 `rowCount/columnCount` 收缩必须满足 `rowCount >= frozenRowCount + 1`、`columnCount >= frozenColumnCount + 1`，杜绝结构性 400。
- **冻结与表头一致性**：币种查询子表冻结行列、表头背景色、wrapStrategy（不自动换行，溢出显示）一致；目录 RichText startIndex 不因 emoji/换行漂移。
- **观测与自检（可选）**：提供只读自检输出（tab 的 gridProperties、style_signature、最后错误），降低排障成本。

## Out of Scope（不做）

- 不修改指标数据口径、不改变卡片字段定义与排序规则。
- 不改“主看板 v5”的布局（除非抽取的共享不变量需要统一）。
- 不引入新基础设施（Redis/Kafka/Apps Script 等）。

## 执行顺序（强制）

1. `CONTEXT.md`（现状证据与风险图谱）
2. `PLAN.md`（方案对比与回滚协议）
3. `TODO.md`（逐条执行 + 验证门禁）
4. `ACCEPTANCE.md`（验收断言对照）
5. `STATUS.md`（命令与证据留存）

