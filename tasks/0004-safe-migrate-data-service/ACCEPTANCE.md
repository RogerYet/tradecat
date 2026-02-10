# ACCEPTANCE - data-service 安全迁移验收标准

## A. 原子断言（Atomic Assertions）

### A1. 源仓库只读不污染

- [ ] 源仓库业务代码未被修改  
  - Verify: `cd /home/lenovo/.projects/tradecat && git diff --name-only -- services/data-service`  
  - Gate: 输出为空

- [ ] 源仓库生产配置与关键数据未被写入  
  - Verify: `stat /home/lenovo/.projects/tradecat/config/.env`（迁移前后对比）  
  - Gate: `STATUS.md` 记录迁移前后 mtime/size/hash，不发生变化

### A2. 迁移目录结构正确（防止 PROJECT_ROOT 推导错误）

- [ ] 目标服务路径为：`/home/lenovo/tradecat/services/data-service`  
  - Verify: `test -f /home/lenovo/tradecat/services/data-service/src/config.py && echo OK`
  - Gate: OK

- [ ] 目标结构存在默认输出目录（避免落到异常路径）  
  - Verify: `test -d /home/lenovo/tradecat/libs/database/csv && echo OK`
  - Gate: OK

### A3. 最小可运行（不要求依赖齐全）

- [ ] 在目标目录执行帮助命令可成功  
  - Verify: `cd /home/lenovo/tradecat/services/data-service && python3 src/__main__.py --help`
  - Gate: 退出码为 0，且输出包含 `--ws/--metrics/--backfill/--all` 任一关键参数

## B. 边缘路径（至少 3 个）

1) 目标目录不存在 `config/.env`：帮助命令仍可运行（不应强制依赖 DB）。  
2) 目标目录缺少 third-party 依赖：帮助命令仍可运行（不触发 collectors import）。  
3) 误把服务复制到 `migrated/`：`PROJECT_ROOT` 推导错误，应被 `TODO.md` 的 Gate 阻断。  

## C. 禁止性准则（Anti-Goals）

- 不允许复制源仓库 `.env` 到目标（避免密钥外泄与污染）。
- 不允许复制源仓库 `*.db` 到目标（避免把旧数据当成真相源）。
- 不允许在源仓库目录下生成任何新日志/缓存目录。

