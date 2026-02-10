# TODO - 微步骤执行清单

> 每一行都必须可验证（Verify），且有准入门槛（Gate）。

[ ] P0: 初始化任务目录与索引 | Verify: `ls -la tasks | grep 0002` | Gate: 目录存在且包含 6 个文档
[ ] P0: 冻结“维度模型”作为治理面 | Verify: `grep -n \"维度模型\" tasks/0002-governance-constitution-and-gates/CONTEXT.md` | Gate: 维度列表 ≥ 8 且每个维度有治理意图
[ ] P0: 固化宪法 v1 的 MUST 列表映射到门禁清单 | Verify: `grep -n \"系统宪法\" tasks/0002-governance-constitution-and-gates/PLAN.md` | Gate: 至少 4 类门禁 + 失败输出规范
[ ] P0: 定义门禁落地点（本地 + CI） | Verify: `grep -n \"CI\" tasks/0002-governance-constitution-and-gates/PLAN.md` | Gate: 明确指出将修改哪个 workflow/脚本入口

[ ] P1: 定义时间语义最小对齐用例（≥3） | Verify: `grep -n \"时间语义\" tasks/0002-governance-constitution-and-gates/ACCEPTANCE.md` | Gate: 用例覆盖对齐边界/晚到/缺口传播
[ ] P1: 定义幂等键声明的“唯一入口” | Verify: `grep -n \"幂等\" tasks/0002-governance-constitution-and-gates/PLAN.md` | Gate: 声明“写点集中”与“必须声明幂等键”
[ ] P1: 定义可观测三指标公式与字段来源 | Verify: `grep -n \"延迟\\|缺口\\|重复\" tasks/0002-governance-constitution-and-gates/PLAN.md` | Gate: 每项指标给出公式 + 聚合维度

[ ] P2: 定义豁免机制与审计记录位置 | Verify: `grep -n \"豁免\" tasks/0002-governance-constitution-and-gates/PLAN.md` | Gate: 有开关名 + 记录要求 + 恢复约束
[ ] P2: 形成执行 Agent 的“最小修复指南”模板 | Verify: `grep -n \"最小修复建议\" tasks/0002-governance-constitution-and-gates/PLAN.md` | Gate: 失败输出规范包含修复提示

Parallelizable:
- P1 的时间语义用例、幂等键入口、三指标口径可以并行完善（互不阻塞）。

