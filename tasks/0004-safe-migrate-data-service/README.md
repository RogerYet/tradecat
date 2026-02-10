# 0004 - safe-migrate-data-service

第一批迁移目标只聚焦 **数据采集模块**：将源仓库的 `services/data-service` 安全迁移到新结构中，并把“路径/配置/写入”从源仓库彻底隔离，确保迁移可重复、可回滚、可证伪。

## In Scope

- 源：`/home/lenovo/.projects/tradecat/services/data-service/`（只读）
- 目标：`/home/lenovo/tradecat/services/data-service/`
- 迁移策略：Lift-and-Shift（先拷贝可运行，再逐步收敛到 `tradecat/ingestion/`）
- 关键验证：
  - 新结构中运行 `python3 src/__main__.py --help` 能正常输出用法（不要求依赖齐全）
  - 证明不会读取/写入源仓库：`.projects/tradecat/config/.env` 与 `libs/database/**` 不被污染

## Out of Scope

- 不迁移/不修改 `aws-service`
- 不在本任务里做采集逻辑重写（只做安全迁移与隔离）
- 不修改源仓库任何业务代码

## 阅读与执行顺序（必须严格遵守）

1. `CONTEXT.md`
2. `PLAN.md`
3. `ACCEPTANCE.md`
4. `TODO.md`
5. `STATUS.md`

