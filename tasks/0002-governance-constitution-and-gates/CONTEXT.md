# CONTEXT - 维度模型驱动的长期治理

## 1) 现状追溯（基于可验证证据）

当前仓库已存在三份“治理核心文档雏形”：

- 宪法草案：`docs/architecture/CONSTITUTION.md`  
  - 关键条目位置：`grep -n "^## 2\\. 系统宪法" docs/architecture/CONSTITUTION.md` → `34:...`  
  - 单向依赖条目：`grep -n "单向依赖" docs/architecture/CONSTITUTION.md | head` → `38:...`
- 分层契约：`docs/analysis/layer_contract_one_pager.md`  
  - 采集层段落：`grep -n '^## 1)' docs/analysis/layer_contract_one_pager.md`（错误示例：不要写 `\\)`，会触发 “Unmatched )”）  
  - 可用定位：`grep -n '^## 1)' docs/analysis/layer_contract_one_pager.md` → `17:...`
- 目录结构设计：`docs/analysis/repo_structure_design.md`  
  - 理想形态段落：`grep -n "^## 2\\. 理想形态" docs/analysis/repo_structure_design.md` → `21:...`

此外，存在一个“新版本骨架路径”（用于未来迁移）：

- `/home/lenovo/tradecat/tradecat`（WSL 路径，对应用户指定的 `\\wsl.localhost\\Ubuntu\\home\\lenovo\\tradecat\\tradecat`）  
  - 证据：`ls -la /home/lenovo/tradecat/tradecat | head`

## 2) 约束矩阵（必须遵守）

| 约束 | 来源 | 影响 |
| :-- | :-- | :-- |
| 禁止修改 `config/.env` | `AGENTS.md`（`grep -n "禁止修改" AGENTS.md | head` → 22 行附近） | 所有变更必须通过 `.env.example` 与文档描述，或使用新变量默认值 |
| 禁止随意改 DB schema（除非明确要求） | `AGENTS.md`（同上） | 本任务的“门禁”应先从契约/边界/观测入手，schema 演进需另立任务或显式授权 |
| 禁止添加未经验证第三方依赖 | `AGENTS.md` | 门禁优先用自研脚本/现有工具链实现 |

## 3) 维度模型（从“维度”治理复杂度，而不是从“模块”治理）

本任务以维度划分治理面（每个维度都对应“统一口径 + 强制门禁”）：

1. **数据维度（Data Model）**：Raw/Derived/Signal 的最小字段集合与语义，禁止各服务自造口径。
2. **时间维度（Time Semantics）**：UTC + 对齐锚点 + 窗口边界；禁止隐式时区与混乱对齐。
3. **写入维度（Write Ownership）**：谁能写 raw_* / derived_* / delivery_*；写点集中，便于审计与幂等。
4. **幂等维度（Idempotency）**：至少一次交付前提下，写入必须声明幂等键（upsert/insert-ignore）。
5. **质量维度（Quality Facts）**：缺口/晚到/过期/输入不完整必须可表达（quality_flags）。
6. **可观测维度（Observability）**：延迟/缺口率/重复率三指标必须可计算并输出。
7. **依赖维度（Dependency Graph）**：三层单向依赖 + 反向依赖禁止；循环依赖必须在 CI 阻断。
8. **演进维度（Versioning & Migration）**：契约破坏必须版本化；必须有回滚开关与弃用期。
9. **安全与配置维度（Security & Config）**：密钥不可入库/不可入 Git；配置集中与可审计。

## 4) 风险量化表

| 风险点 | 严重程度 | 触发信号 (Signal) | 缓解方案 (Mitigation) |
| :--- | :---: | :--- | :--- |
| 门禁过强导致开发停摆 | High | 大量 PR 失败且无清晰错误信息 | 门禁输出必须可读（给出违规文件/依赖链）；提供临时豁免开关但必须记录理由 |
| 宪法/契约变成“口号文档” | High | 规则存在但 CI 不检查 | 把关键条目转成脚本检查项（依赖边界/幂等键声明/UTC 检查） |
| 共享模块演化为泥团 | Medium | `common/utils` 变大、跨层 import 增多 | 宪法硬禁 + import 边界检查；共享只允许“薄而硬”基础能力 |
| 新旧版本双轨失控 | Medium | 同一概念在两处实现且口径不同 | 以契约为唯一真相；新旧都必须对齐同一契约版本 |

## 5) 假设与证伪（最小假设推进）

| 假设 | 默认假设 | 证伪命令（必须可运行） |
| :-- | :-- | :-- |
| 宪法/契约/结构文档已存在且可作为 v1 输入 | 是 | `ls -la docs/architecture && ls -la docs/analysis | head` |
| 新版本骨架目录存在（用于未来迁移） | 是 | `ls -la /home/lenovo/tradecat/tradecat | head` |
| 不引入新依赖也能实现第一版门禁 | 是 | `find . -maxdepth 2 -type f -name "*.py" -print | head`（确认可用 Python 脚本承载） |
