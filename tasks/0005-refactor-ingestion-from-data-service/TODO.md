# TODO - 执行清单（给执行 Agent）

[ ] P0: 固化旧实现“基线语义” | Verify: `nl -ba services/data-service/src/adapters/cryptofeed.py | sed -n '40,60p'` | Gate: 明确 `timestamp=candle.start`
[ ] P0: 在新结构创建 ingestion 模块骨架 | Verify: `find /home/lenovo/tradecat/tradecat/ingestion -maxdepth 3 -type f | wc -l` | Gate: providers/jobs/storage/cli 至少各 1 个文件
[ ] P0: 迁移 COPY+temp-table 写入策略 | Verify: `rg -n \"COPY\" /home/lenovo/tradecat/tradecat/ingestion -S` | Gate: storage 存在 COPY 写入实现

[ ] P1: 跑通 WS 1m 最小闭环（单币种） | Verify: `python -m tradecat.ingestion ws-1m --symbols BTCUSDT --once` | Gate: DB 有数据 + 日志有写入条数
[ ] P1: 跑通 gap scan/backfill（短时间窗） | Verify: `python -m tradecat.ingestion backfill --symbols BTCUSDT --days 2` | Gate: gap_found 或 filled 计数可观测
[ ] P1: 跑通 futures metrics 5m（单币种） | Verify: `python -m tradecat.ingestion futures-metrics --symbols BTCUSDT --once` | Gate: DB 写入成功或可读失败

[ ] P1: 对齐验证（旧 vs 新） | Verify: `python -m tradecat.ingestion verify-align --symbol BTCUSDT --interval 1m --start ... --end ...` | Gate: 三条对齐断言全部通过

[ ] P2: 幂等验证（重复跑不增量） | Verify: 重复执行一次 ws-1m once | Gate: row count 不增长或 upsert_conflict 可观测
[ ] P2: 安全验证（不污染源仓库） | Verify: `sha256sum /home/lenovo/.projects/tradecat/config/.env` | Gate: hash 不变

Parallelizable:
- futures-metrics 与 backfill 可并行开发（共享 storage）。

