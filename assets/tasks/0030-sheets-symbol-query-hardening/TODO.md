# TODO：逐条执行清单（可验证）

> 格式：`[ ] Px: 动作 | Verify: 命令/检查 | Gate: 准入（对应 ACCEPTANCE）`

## P0（必须）

- [ ] P0: 审计所有网格收缩入口（调用 `_set_sheet_grid_properties` 的位置） | Verify: `rg -n \"_set_sheet_grid_properties\\(\" services/consumption/sheets-service/src/sa_sheets_writer.py` | Gate: 形成“调用点清单”写入 `STATUS.md`
- [ ] P0: 在 `_set_sheet_grid_properties` 内收敛不变量（row/col 必须 > frozen） | Verify: 运行 A2 脚本断言 `rowCount>=frozenRowCount+1 && colCount>=frozenColumnCount+1` | Gate: `ACCEPTANCE.A2`
- [ ] P0: 修复币种查询 `need_style` 锁死（引入 `style_signature` 或 bump 机制 + compact grid 下 meta 对齐 n_rows/n_cols） | Verify: `rg -n \"style_signature|symbol_table_v\" services/consumption/sheets-service/src/sa_sheets_writer.py` | Gate: `ACCEPTANCE.A3`
- [ ] P0: 在 `write_symbol_query_tab` 的 compact grid 调用点增加最小纠偏（防止传入非法 row/col） | Verify: `rg -n \"want_rows|want_cols\" services/consumption/sheets-service/src/sa_sheets_writer.py` | Gate: `ACCEPTANCE.A1`
- [ ] P0: 冒烟跑通一次强制刷新（SA 模式） | Verify: `cd services/consumption/sheets-service && python -m src --once --force --write-mode sa --lang zh_CN` | Gate: `ACCEPTANCE.A1`

## P1（推荐）

- [ ] P1: 增加只读自检入口（`--doctor`）：输出每个 symbol tab 的 gridProperties/style_signature/最后错误 | Verify: `cd services/consumption/sheets-service && python -m src --doctor | head` | Gate: 输出包含 `币种查询_` tab 列表
- [ ] P1: 将“纠偏发生/400/429/SSL 抖动”写成单行摘要日志（可 grep） | Verify: `rg -n \"symtab\\.grid_clamp|HttpError 400|SSLError\" services/consumption/sheets-service/logs` | Gate: 排障时 30s 内定位问题
- [ ] P1: 为目录 RichText 写入失败提供可观测降级（退化为纯文本但不抛 400） | Verify: 人为注入 emoji/长目录后运行 A1 | Gate: `ACCEPTANCE.B3`

## P2（可选）

- [ ] P2: 将 grid 不变量抽成共享工具，复用到 dashboard/Polymarket 的 compact grid | Verify: `rg -n \"compact grid\" services/consumption/sheets-service/src/sa_sheets_writer.py` | Gate: 不新增重复 clamp 逻辑
- [ ] P2: 在 `assets/config/.env.example` 增补本任务新增/关键 env 说明（compact grid/style_signature/doctor） | Verify: `rg -n \"SYMBOL_QUERY_COMPACT_GRID|doctor\" assets/config/.env.example` | Gate: 文档与模板一致

